"""Resumable development runner. Requires the repo's pinned GPU environment."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from rules.evidence import FIELDS, LABELS, resolve, validate_record

ORDERS = {
    "forward": ("MEETS", "FAILS", "NEEDS_INFO"),
    "reverse": ("NEEDS_INFO", "FAILS", "MEETS"),
    "cycle1": ("FAILS", "NEEDS_INFO", "MEETS"),
    "cycle2": ("NEEDS_INFO", "MEETS", "FAILS"),
    "reverse_cycle1": ("FAILS", "MEETS", "NEEDS_INFO"),
    "reverse_cycle2": ("MEETS", "NEEDS_INFO", "FAILS"),
}
METHODS = ("plain", "fact_table", "extract_rule")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_prompt(packet: str, item: dict, method: str, order: str) -> str:
    if method not in METHODS or order not in ORDERS:
        raise ValueError("unknown method or order")
    # Never include full_record, gold, profile, condition or oracle questions.
    case = item["case_text"]
    if method == "fact_table":
        case = json.dumps(item["record"], sort_keys=True)
    body = (packet.strip() + "\n\nVERIFIED RECORD\n" + case
            + "\n\nUNVERIFIED CHARACTER NOTE\n" + item["character_note"])
    if method == "extract_rule":
        schema = '{"paid_work_hours": integer_or_null, "approved_program_hours": integer_or_null, "medical_exemption": boolean_or_null}'
        return (body + "\n\nExtract only the three legal fields from the verified record. "
                "Preserve an UNKNOWN field as null. Use integer hours and JSON booleans. "
                "Explain briefly if needed, then end with FACTS: followed by one JSON object "
                "with exactly this schema: " + schema)
    return (body + "\n\nDetermine the condition using the verified record. Explain briefly if needed. "
            "End with one line ANSWER: followed by exactly one of "
            + ", ".join(ORDERS[order]) + ".")


def final_text(text: str, require_separator: bool = False) -> str | None:
    for marker in ("</think>", "<|channel|>final<|message|>", "assistantfinal"):
        if marker in text:
            return text.rsplit(marker, 1)[1].strip()
    return None if require_separator else text.strip()


def parse(text: str, method: str, require_separator: bool = False,
          finish_reason: str | None = None) -> tuple[str, dict | None]:
    if finish_reason == "length":
        return "TRUNCATED", None
    final = final_text(text, require_separator)
    if final is None:
        return "TRUNCATED", None
    if method == "extract_rule":
        if "FACTS:" not in final:
            return "INVALID", None
        payload = final.rsplit("FACTS:", 1)[1].strip()
        try:
            record = json.loads(payload)
            validate_record(record)
            if set(record) != set(FIELDS):
                return "INVALID", None
            return resolve(record)["label"], record
        except (ValueError, TypeError):
            return "INVALID", None
    answers = re.findall(r"^ANSWER:\s*(MEETS|FAILS|NEEDS_INFO)\s*$", final, flags=re.M)
    # Multiple conflicting final lines are not silently resolved by taking the last.
    return (answers[0], None) if len(answers) == 1 else ("INVALID", None)


def validate_manifest(data: Path, packet: Path) -> dict:
    manifest = json.loads(Path(str(data) + ".manifest.json").read_text())
    if manifest["sha256"] != sha(data) or manifest["packet_sha256"] != sha(packet):
        raise ValueError("Dataset or packet changed after manifest generation")
    for key, source in (("oracle_sha256", ROOT / "src/rules/evidence.py"),
                        ("generator_sha256", ROOT / "src/gen/make_evidence_pilot.py")):
        if manifest.get(key) is not None and manifest[key] != sha(source):
            raise ValueError("Source changed after generation; regenerate development data")
    if manifest.get("confirmatory") is not False:
        raise ValueError("This runner is for development; freeze a separate held-out protocol before main experiments")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--data", type=Path, default=ROOT / "data/evidence_pilot/dev.jsonl")
    p.add_argument("--packet", type=Path, default=ROOT / "configs/evidence_packet.md")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--method", choices=METHODS, default="plain")
    p.add_argument("--seeds", default="0")
    p.add_argument("--orders", default="forward,reverse")
    p.add_argument("--cue", default="all")
    p.add_argument("--base-limit", type=int)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--max-num-seqs", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--thinking", choices=("on", "off"), default="on")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if min(args.max_tokens, args.max_num_seqs, args.batch_size) <= 0:
        p.error("token, sequence and batch settings must be positive")
    if args.max_model_len <= args.max_tokens:
        p.error("max-model-len must leave room for the prompt")
    manifest = validate_manifest(args.data, args.packet)
    items = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()]
    if len({r["item_id"] for r in items}) != len(items):
        raise ValueError("duplicate dataset item IDs")
    seeds = [int(s) for s in args.seeds.split(",")]
    orders = args.orders.split(",")
    if len(set(seeds)) != len(seeds) or len(set(orders)) != len(orders) or set(orders)-set(ORDERS):
        p.error("duplicate seeds/orders or unknown order")
    bases = sorted({r["base"] for r in items})
    if args.base_limit is not None:
        if args.base_limit < 1:
            p.error("base-limit must be positive")
        bases = bases[:args.base_limit]
    if args.cue != "all" and args.cue not in {r["cue"] for r in items}:
        p.error("unknown cue")
    items = [r for r in items if r["base"] in bases and (args.cue == "all" or r["cue"] == args.cue)]
    packet = args.packet.read_text()
    jobs = [dict(item=r, order=o, seed=s,
                 request_id=f"{r['item_id']}|{args.method}|{o}|{s}",
                 prompt=build_prompt(packet, r, args.method, o))
            for r in items for o in orders for s in seeds]
    if args.dry_run:
        print(json.dumps(dict(stage="development", confirmatory=False, model=args.model,
                             n_items=len(items), n_requests=len(jobs),
                             examples=[dict(request_id=j["request_id"], prompt=j["prompt"])
                                       for j in jobs[:2]]), indent=2))
        return
    import yaml
    models = {m["id"]: m for m in yaml.safe_load((ROOT / "configs/models.yaml").read_text())["models"]}
    if args.model not in models or not (args.model.startswith("qwen3") or args.model == "gpt-oss-20b"):
        p.error("supported: pinned Qwen3 models and gpt-oss-20b; validate other-family adapters separately")
    model = models[args.model]
    if args.model == "gpt-oss-20b" and args.thinking == "off":
        p.error("gpt-oss is an always-reasoning model")
    meta_path = Path(str(args.out) + ".meta.json")
    settings = dict(
        stage="development", confirmatory=False, model=args.model, revision=model["revision"],
        data_sha256=sha(args.data), packet_sha256=sha(args.packet),
        runner_sha256=sha(Path(__file__)), oracle_sha256=sha(ROOT / "src/rules/evidence.py"),
        engine_sha256=sha(ROOT / "src/rules/snap.py"), method=args.method, seeds=seeds, orders=orders,
        cue=args.cue, bases=bases, thinking=args.thinking,
        max_tokens=args.max_tokens, max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs, batch_size=args.batch_size,
        temperature=1.0 if args.model == "gpt-oss-20b" else .6,
        top_p=1.0 if args.model == "gpt-oss-20b" else .95,
        top_k=-1 if args.model == "gpt-oss-20b" else 20,
        gpu_memory_utilization=.90, n_requests=len(jobs),
    )
    protocol_sha256 = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    done = set()
    if args.out.exists():
        if not args.resume:
            raise ValueError("output exists; use --resume or a new path")
        if json.loads(meta_path.read_text())["settings"] != settings:
            raise ValueError("resume settings differ from original run")
        for line in args.out.read_text().splitlines():
            row = json.loads(line)
            if row["request_id"] in done:
                raise ValueError("duplicate resume request")
            done.add(row["request_id"])
        if done - {j["request_id"] for j in jobs}:
            raise ValueError("resume file contains unexpected requests")
    pending = [j for j in jobs if j["request_id"] not in done]
    if not pending:
        print(json.dumps(dict(done=len(done), remaining=0)))
        return
    import torch
    import transformers
    import vllm
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    template = {"enable_thinking": args.thinking == "on"} if args.model.startswith("qwen3") else {"reasoning_effort": "medium"}
    tokenizer = AutoTokenizer.from_pretrained(model["repo"], revision=model["revision"])
    for job in pending:
        tokens = tokenizer.apply_chat_template(
            [{"role": "user", "content": job["prompt"]}], tokenize=True,
            add_generation_prompt=True, **template)
        if len(tokens) + args.max_tokens > args.max_model_len:
            raise ValueError("prompt plus output budget exceeds context length")
    llm = LLM(model=model["repo"], revision=model["revision"],
              dtype=model["dtype"] if model["dtype"] == "bfloat16" else "auto",
              max_model_len=args.max_model_len, max_num_seqs=args.max_num_seqs,
              gpu_memory_utilization=.90, seed=0, enable_prefix_caching=True)
    runtime = dict(python=platform.python_version(), torch=torch.__version__,
                   transformers=transformers.__version__, vllm=vllm.__version__,
                   gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.out.exists():
        meta_path.write_text(json.dumps(dict(settings=settings, runtime=runtime,
                                            dataset_manifest=manifest), indent=2) + "\n")
    with args.out.open("a") as handle:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start+args.batch_size]
            conversations = [[{"role": "user", "content": j["prompt"]}] for j in batch]
            sampling = [SamplingParams(temperature=settings["temperature"],
                                       top_p=settings["top_p"], top_k=settings["top_k"],
                                       max_tokens=args.max_tokens, seed=j["seed"]) for j in batch]
            generated = llm.chat(conversations, sampling, use_tqdm=True,
                                 add_generation_prompt=True, chat_template_kwargs=template)
            if len(generated) != len(batch):
                raise ValueError("generation count mismatch")
            for job, output in zip(batch, generated):
                completion = output.outputs[0]
                decision, extracted = parse(completion.text, args.method,
                                            require_separator=args.thinking == "on",
                                            finish_reason=completion.finish_reason)
                row = dict(request_id=job["request_id"], item_id=job["item"]["item_id"],
                           model=args.model, revision=model["revision"],
                           data_sha256=settings["data_sha256"], packet_sha256=settings["packet_sha256"],
                           protocol_sha256=protocol_sha256,
                           method=args.method, order=job["order"], seed=job["seed"],
                           decision=decision, extracted_record=extracted,
                           finish_reason=completion.finish_reason, output=completion.text,
                           output_tokens=len(completion.token_ids))
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            print(json.dumps(dict(written=len(done)+min(start+len(batch), len(pending)),
                                  total=len(jobs))), flush=True)


if __name__ == "__main__":
    main()
