"""Frontier replicate of ladder cells through APIs (2026-10-12). Same items, prompt composition and parser as
src/run/run_evidence_pilot.py (imported), same output row format, so score_evidence_ladder.py scores the file unchanged.
Providers: OpenAI Responses API (reasoning effort medium; no reasoning text returned) and Anthropic Messages API
(adaptive thinking, display summarized, effort as given; the packet prefix is cached). Resumable: rows already in --out are
skipped. No fallback model: a refusal or API error is recorded as such.

Usage: python src/run/run_evidence_api.py --model gpt-5-2025-08-07 --data data/evidence_ladder/dev.jsonl \
          --filter "surface=S2,condition=missing_material" --orders forward --out results/evidence_ladder/gpt-5_plain.jsonl
Credentials: OPENAI_API_KEY / ANTHROPIC_API_KEY in the environment (never in the repo).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/run"))
from run_evidence_pilot import ORDERS, METHODS, build_prompt, parse, pathway_of, sha, validate_manifest  # noqa: E402

PROVIDER = {"claude": "anthropic", "gpt": "openai", "o1": "openai", "o3": "openai", "o4": "openai"}


def call_openai(client, model, prompt, max_tokens, effort):
    r = client.responses.create(model=model, input=prompt, reasoning={"effort": effort}, max_output_tokens=max_tokens)
    finish = "length" if getattr(r, "incomplete_details", None) else getattr(r, "status", "completed")
    usage = getattr(r, "usage", None)
    return r.output_text, finish, getattr(usage, "output_tokens", 0) if usage else 0


def call_anthropic(client, model, prompt, max_tokens, effort):
    head, sep, tail = prompt.partition("\n\nVERIFIED RECORD\n")
    if not sep:
        head, sep, tail = prompt.partition("\n\nCASE FILE\n")
    content = ([{"type": "text", "text": head, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": sep + tail}] if sep else prompt)
    r = client.messages.create(model=model, max_tokens=max_tokens,
                               thinking={"type": "adaptive", "display": "summarized"},
                               output_config={"effort": effort},
                               messages=[{"role": "user", "content": content}])
    text = "\n".join(b.text for b in r.content if b.type == "text")
    think = "\n".join(getattr(b, "thinking", "") or "" for b in r.content if b.type == "thinking")
    # Keep the parser's separator convention: thinking (if any) before </think>, answer after.
    full = (f"<think>\n{think}\n</think>\n" if think else "") + text
    return full, r.stop_reason, r.usage.output_tokens


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--data", type=Path, default=ROOT / "data/evidence_ladder/dev.jsonl")
    p.add_argument("--packet", type=Path, default=ROOT / "configs/evidence_packet.md")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--method", choices=("plain",), default="plain")
    p.add_argument("--orders", default="forward")
    p.add_argument("--filter", default=None)
    p.add_argument("--base-limit", type=int)
    p.add_argument("--effort", default=None, help="openai reasoning effort (default medium) / anthropic effort (default high)")
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    provider = next((v for k, v in PROVIDER.items() if a.model.startswith(k)), None)
    if not provider:
        p.error("model must start with claude / gpt / o1 / o3 / o4")
    effort = a.effort or ("medium" if provider == "openai" else "high")
    manifest = validate_manifest(a.data, a.packet)
    items = [json.loads(l) for l in a.data.read_text().splitlines() if l.strip()]
    bases = sorted({r["base"] for r in items})
    if a.base_limit:
        bases = bases[:a.base_limit]
    filters = {}
    for part in filter(None, (a.filter or "").split(",")):
        k, _, v = part.partition("=")
        filters[k] = set(v.split("|"))
    items = [r for r in items if r["base"] in bases and all(str(r.get(k)) in v for k, v in filters.items())]
    orders = a.orders.split(",")
    packet_names = sorted({r.get("packet") or "__default__" for r in items})
    packets = {n: (a.packet if n == "__default__" else ROOT / "configs" / n).read_text() for n in packet_names}
    packet_hashes = {n: sha(a.packet if n == "__default__" else ROOT / "configs" / n) for n in packet_names}
    jobs = [dict(item=r, order=o, request_id=f"{r['item_id']}|{a.method}|{o}|api",
                 prompt=build_prompt(packets[r.get("packet") or "__default__"], r, a.method, o))
            for r in items for o in orders][: a.limit]
    done = set()
    if a.out.exists():
        done = {json.loads(l)["request_id"] for l in a.out.read_text().splitlines() if l.strip()}
    pending = [j for j in jobs if j["request_id"] not in done]
    settings = dict(stage="development", confirmatory=False, model=a.model, provider=provider, effort=effort,
                    data_sha256=sha(a.data), packet_sha256=packet_hashes.get("__default__", sha(a.packet)),
                    packets=packet_hashes, filters={k: sorted(v) for k, v in filters.items()}, method=a.method,
                    orders=orders, bases=bases, max_tokens=a.max_tokens, n_requests=len(jobs))
    protocol = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    print(json.dumps(dict(model=a.model, n_items=len(items), n_requests=len(jobs), done=len(done), pending=len(pending))))
    if a.dry_run:
        print(pending[0]["prompt"] if pending else "nothing pending")
        return
    if provider == "openai":
        import openai
        client, call = openai.OpenAI(max_retries=5), call_openai
    else:
        import anthropic
        client, call = anthropic.Anthropic(max_retries=5), call_anthropic
    a.out.parent.mkdir(parents=True, exist_ok=True)
    meta_path = Path(str(a.out) + ".meta.json")
    if not meta_path.exists():
        meta_path.write_text(json.dumps(dict(settings=settings, dataset_manifest=manifest), indent=2) + "\n")
    lock = threading.Lock()
    t0 = time.time()

    def one(job):
        item = job["item"]
        try:
            text, finish, n = call(client, a.model, job["prompt"], a.max_tokens, effort)
        except Exception as e:
            return dict(request_id=job["request_id"], item_id=item["item_id"], model=a.model, revision=a.model,
                        data_sha256=settings["data_sha256"], packet_sha256=settings["packet_sha256"], protocol_sha256=protocol,
                        method=a.method, order=job["order"], seed="api", decision="ERROR", extracted_record=None,
                        finish_reason=f"error: {type(e).__name__}: {str(e)[:200]}", output="", output_tokens=0)
        decision, payload = parse(text, a.method, require_separator=False,
                                  finish_reason="length" if finish in ("length", "max_tokens") else None,
                                  pathway=pathway_of(item))
        if finish == "refusal":
            decision = "REFUSAL"
        return dict(request_id=job["request_id"], item_id=item["item_id"], model=a.model, revision=a.model,
                    data_sha256=settings["data_sha256"], packet_sha256=settings["packet_sha256"], protocol_sha256=protocol,
                    method=a.method, order=job["order"], seed="api", decision=decision, extracted_record=None,
                    finish_reason=finish, output=text, output_tokens=n)

    n_written = 0
    with a.out.open("a") as f, ThreadPoolExecutor(a.workers) as ex:
        for fut in as_completed([ex.submit(one, j) for j in pending]):
            row = fut.result()
            with lock:
                f.write(json.dumps(row) + "\n"); f.flush(); os.fsync(f.fileno())
                n_written += 1
                if n_written % 25 == 0:
                    print(json.dumps(dict(written=n_written, pending=len(pending), seconds=round(time.time() - t0))), flush=True)
    print(json.dumps(dict(done=len(done) + n_written, total=len(jobs), seconds=round(time.time() - t0))))


if __name__ == "__main__":
    main()
