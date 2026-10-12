"""Resumable development runner. Requires the repo's pinned GPU environment.

2026-10-12: extended for the ladder set (per-item packet, packet_extra, unlabelled cue surfaces) and the
one-step clarification method `request` (turn 1: ANSWER or REQUEST fields; turn 2: the requested fields are
supplied from the fixed full record and the model gives a final ANSWER). The first development set runs
byte-identically to before (same prompt composition when an item carries no packet / header fields).
"""
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
from rules import evidence as abawd_oracle
from rules import evidence_gross as gross_oracle

LABELS = abawd_oracle.LABELS
ORACLES = {"abawd": abawd_oracle, "gross": gross_oracle}
ORDERS = {
    "forward": ("MEETS", "FAILS", "NEEDS_INFO"),
    "reverse": ("NEEDS_INFO", "FAILS", "MEETS"),
    "cycle1": ("FAILS", "NEEDS_INFO", "MEETS"),
    "cycle2": ("NEEDS_INFO", "MEETS", "FAILS"),
    "reverse_cycle1": ("FAILS", "MEETS", "NEEDS_INFO"),
    "reverse_cycle2": ("MEETS", "NEEDS_INFO", "FAILS"),
}
METHODS = ("plain", "fact_table", "fact_table_stmt", "extract_rule", "request")
REQUESTABLE = {
    "abawd": ("paid_work_hours", "approved_program_hours", "medical_exemption", "preferred_contact_window"),
    "gross": ("household_size", "earned_income", "unearned_income", "preferred_contact_window"),
}
PROVENANCE = {
    "paid_work_hours": "employer pay records on file", "approved_program_hours": "attendance record on file",
    "medical_exemption": "physician's certification on file", "preferred_contact_window": "intake form",
    "household_size": "intake form", "earned_income": "employer pay records on file",
    "unearned_income": "benefit award letters on file",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pathway_of(item: dict) -> str:
    return item.get("pathway", "abawd")


def legal_record(item: dict, record: dict) -> dict:
    if pathway_of(item) == "abawd":
        return {k: record[k] for k in abawd_oracle.FIELDS}
    return {k: record[k] for k in ("household_size",) + gross_oracle.FIELDS}


def answer_labels(order: str, method: str) -> tuple[str, ...]:
    labels = ORDERS[order]
    return tuple(l for l in labels if l != "NEEDS_INFO") if method == "request" else labels


def build_prompt(packet: str, item: dict, method: str, order: str) -> str:
    if method not in METHODS or order not in ORDERS:
        raise ValueError("unknown method or order")
    # Never include full_record, gold, profile, condition or oracle questions.
    case = item["case_text"]
    if method in ("fact_table", "fact_table_stmt"):
        # The exact partial record, nulls preserved, as a machine-readable table (no narrative).
        case = json.dumps(item["record"], sort_keys=True)
        if method == "fact_table_stmt" and item.get("self_report_claim") is not None:
            # 2026-10-12 (external review 2, item 3): the same correct record plus the applicant's statement,
            # so that the decision step is tested with the facts already right.
            pivot = item["pivot"]
            claim = item["self_report_claim"]
            shown = (f"${claim:,}" if pivot in ("earned_income", "unearned_income") else str(claim))
            status = "requested and not yet received" if item.get("evidence") == "E3s" else "not on file"
            case += ("\nStatements on file (not part of the verified record): the applicant states "
                     + (f"{pivot} = {shown}" if pivot != "medical_exemption" else "that a doctor has certified them unfit for work")
                     + f"; the supporting record is {status}.")
    text = packet.strip()
    if item.get("packet_extra"):
        text += "\n\n" + item["packet_extra"].strip()
    body = text + "\n\n" + item.get("record_header", "VERIFIED RECORD") + "\n" + case
    if item.get("character_note"):
        body += "\n\nUNVERIFIED CHARACTER NOTE\n" + item["character_note"]
    if method == "extract_rule":
        if pathway_of(item) == "abawd":
            schema = '{"paid_work_hours": integer_or_null, "approved_program_hours": integer_or_null, "medical_exemption": boolean_or_null}'
            fields = "the three legal fields"
        else:
            schema = '{"household_size": integer, "earned_income": integer_or_null, "unearned_income": integer_or_null}'
            fields = "the household size and the two income fields"
        return (body + f"\n\nExtract only {fields} from the verified record. "
                "Preserve an UNKNOWN or unlisted field as null; do not use the applicant's own statements. "
                "Use integers and JSON booleans. Explain briefly if needed, then end with FACTS: followed by one JSON object "
                "with exactly this schema: " + schema)
    if method == "request":
        fields = ", ".join(REQUESTABLE[pathway_of(item)])
        return (body + "\n\nDetermine the condition using the verified record. Explain briefly if needed. "
                "If the verified record does not settle the determination, do not guess: end with one line "
                "REQUEST: followed by the names of the fields whose verification you need, comma-separated, chosen from "
                + fields + ". If the verified record settles it, end with one line ANSWER: followed by exactly one of "
                + ", ".join(answer_labels(order, method)) + ".")
    return (body + "\n\nDetermine the condition using the verified record. Explain briefly if needed. "
            "End with one line ANSWER: followed by exactly one of "
            + ", ".join(ORDERS[order]) + ".")


def verification_message(item: dict, requested: list[str], order: str) -> tuple[str, dict]:
    """Supply the requested fields from the fixed full record (never from a model)."""
    full = item["full_record"]
    lines, record = [], dict(item["record"])
    for field in requested:
        value = full[field]
        if field == "medical_exemption":
            shown = "APPLIES" if value else "DOES NOT APPLY"
        elif field in ("earned_income", "unearned_income"):
            shown = f"${value:,}"
        else:
            shown = str(value)
        lines.append(f"- {field}: {shown} ({PROVENANCE[field]})")
        record[field] = value
    message = ("Verification received for the requested fields:\n" + "\n".join(lines)
               + "\n\nGive your final determination using the verified record as now established. "
               "End with one line ANSWER: followed by exactly one of " + ", ".join(answer_labels(order, "request")) + ".")
    return message, record


def final_text(text: str, require_separator: bool = False) -> str | None:
    for marker in ("</think>", "<|channel|>final<|message|>", "assistantfinal"):
        if marker in text:
            return text.rsplit(marker, 1)[1].strip()
    return None if require_separator else text.strip()


def parse(text: str, method: str, require_separator: bool = False,
          finish_reason: str | None = None, pathway: str = "abawd") -> tuple[str, dict | None]:
    """Returns (decision, payload). payload: extracted record (extract_rule) or requested fields (request)."""
    if finish_reason == "length":
        return "TRUNCATED", None
    final = final_text(text, require_separator)
    if final is None:
        return "TRUNCATED", None
    oracle = ORACLES[pathway]
    if method == "extract_rule":
        if "FACTS:" not in final:
            return "INVALID", None
        payload = final.rsplit("FACTS:", 1)[1].strip()
        try:
            record = json.loads(payload)
            oracle.validate_record(record)
            expected = set(oracle.FIELDS) | ({"household_size"} if pathway == "gross" else set())
            if set(record) != expected:
                return "INVALID", None
            return oracle.resolve(record)["label"], record
        except (ValueError, TypeError):
            return "INVALID", None
    if method == "request":
        lines = re.findall(r"^(ANSWER|REQUEST):\s*(.+?)\s*$", final, flags=re.M)
        if len(lines) != 1:
            return "INVALID", None
        kind, value = lines[0]
        if kind == "ANSWER":
            return (value, None) if value in ("MEETS", "FAILS") else ("INVALID", None)
        fields = [f.strip().strip("`'\".") for f in value.split(",")]
        fields = [f for f in fields if f]
        if not fields or len(set(fields)) != len(fields) or set(fields) - set(REQUESTABLE[pathway]):
            return "INVALID", dict(requested_raw=value)
        return "REQUEST", dict(requested=fields)
    answers = re.findall(r"^ANSWER:\s*(MEETS|FAILS|NEEDS_INFO)\s*$", final, flags=re.M)
    # Multiple conflicting final lines are not silently resolved by taking the last.
    return (answers[0], None) if len(answers) == 1 else ("INVALID", None)


def validate_manifest(data: Path, packet: Path) -> dict:
    manifest = json.loads(Path(str(data) + ".manifest.json").read_text())
    if manifest["sha256"] != sha(data):
        raise ValueError("Dataset changed after manifest generation")
    if "packet_sha256_by_name" in manifest:
        for name, digest in manifest["packet_sha256_by_name"].items():
            if sha(ROOT / "configs" / name) != digest:
                raise ValueError(f"Packet {name} changed after manifest generation")
    elif manifest["packet_sha256"] != sha(packet):
        raise ValueError("Packet changed after manifest generation")
    oracles = manifest.get("oracle_sha256_by_name") or {"abawd": manifest.get("oracle_sha256")}
    for name, digest in oracles.items():
        source = ROOT / "src/rules" / ("evidence.py" if name == "abawd" else "evidence_gross.py")
        if digest is not None and digest != sha(source):
            raise ValueError("Oracle changed after generation; regenerate development data")
    generator = ROOT / manifest.get("generator", "src/gen/make_evidence_pilot.py")
    if manifest.get("generator_sha256") is not None and manifest["generator_sha256"] != sha(generator):
        raise ValueError("Generator changed after generation; regenerate development data")
    if manifest.get("confirmatory") is not False:
        raise ValueError("This runner is for development; freeze a separate held-out protocol before main experiments")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--data", type=Path, default=ROOT / "data/evidence_pilot/dev.jsonl")
    p.add_argument("--packet", type=Path, default=ROOT / "configs/evidence_packet.md",
                   help="default packet for items that name none")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--method", choices=METHODS, default="plain")
    p.add_argument("--seeds", default="0")
    p.add_argument("--orders", default="forward,reverse")
    p.add_argument("--cue", default="all")
    p.add_argument("--base-limit", type=int)
    p.add_argument("--filter", default=None,
                   help="comma list of key=value[|value] item filters, e.g. surface=S2,condition=complete|missing_material")
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
    filters = {}
    if args.filter:
        for part in args.filter.split(","):
            key, _, values = part.partition("=")
            filters[key] = set(values.split("|"))
        items = [r for r in items if all(str(r.get(k)) in v for k, v in filters.items())]
    if not items:
        p.error("no items selected")
    packet_names = sorted({r.get("packet") or "__default__" for r in items})
    packets = {name: (args.packet if name == "__default__" else ROOT / "configs" / name).read_text() for name in packet_names}
    packet_hashes = {name: sha(args.packet if name == "__default__" else ROOT / "configs" / name) for name in packet_names}
    jobs = [dict(item=r, order=o, seed=s,
                 request_id=f"{r['item_id']}|{args.method}|{o}|{s}",
                 prompt=build_prompt(packets[r.get("packet") or "__default__"], r, args.method, o))
            for r in items for o in orders for s in seeds]
    if args.dry_run:
        print(json.dumps(dict(stage="development", confirmatory=False, model=args.model,
                             n_items=len(items), n_requests=len(jobs), packets=packet_hashes,
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
        data_sha256=sha(args.data), packet_sha256=packet_hashes.get("__default__", sha(args.packet)),
        packets=packet_hashes, filters={k: sorted(v) for k, v in filters.items()},
        runner_sha256=sha(Path(__file__)), oracle_sha256=sha(ROOT / "src/rules/evidence.py"),
        gross_oracle_sha256=sha(ROOT / "src/rules/evidence_gross.py"),
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

    def sampling_for(batch):
        return [SamplingParams(temperature=settings["temperature"], top_p=settings["top_p"], top_k=settings["top_k"],
                               max_tokens=args.max_tokens, seed=j["seed"]) for j in batch]

    with args.out.open("a") as handle:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start+args.batch_size]
            conversations = [[{"role": "user", "content": j["prompt"]}] for j in batch]
            generated = llm.chat(conversations, sampling_for(batch), use_tqdm=True,
                                 add_generation_prompt=True, chat_template_kwargs=template)
            if len(generated) != len(batch):
                raise ValueError("generation count mismatch")
            rows = []
            for job, output in zip(batch, generated):
                completion = output.outputs[0]
                pathway = pathway_of(job["item"])
                decision, payload = parse(completion.text, args.method, require_separator=args.thinking == "on",
                                          finish_reason=completion.finish_reason, pathway=pathway)
                row = dict(request_id=job["request_id"], item_id=job["item"]["item_id"],
                           model=args.model, revision=model["revision"],
                           data_sha256=settings["data_sha256"], packet_sha256=settings["packet_sha256"],
                           protocol_sha256=protocol_sha256,
                           method=args.method, order=job["order"], seed=job["seed"],
                           decision=decision, extracted_record=payload if args.method == "extract_rule" else None,
                           finish_reason=completion.finish_reason, output=completion.text,
                           output_tokens=len(completion.token_ids))
                if args.method == "request":
                    row.update(requested_fields=(payload or {}).get("requested"),
                               requested_raw=(payload or {}).get("requested_raw"),
                               final_decision=decision if decision in ("MEETS", "FAILS") else None,
                               record_after=None, turn2_output=None, turn2_tokens=None, turn2_finish_reason=None)
                rows.append((job, row))
            second = [(job, row) for job, row in rows if row.get("requested_fields")]
            if second:
                convs, records = [], []
                for job, row in second:
                    message, record = verification_message(job["item"], row["requested_fields"], job["order"])
                    convs.append([{"role": "user", "content": job["prompt"]},
                                  {"role": "assistant", "content": final_text(row["output"]) or row["output"]},
                                  {"role": "user", "content": message}])
                    records.append(record)
                generated2 = llm.chat(convs, sampling_for([j for j, _ in second]), use_tqdm=True,
                                      add_generation_prompt=True, chat_template_kwargs=template)
                if len(generated2) != len(second):
                    raise ValueError("second-turn generation count mismatch")
                for (job, row), record, output in zip(second, records, generated2):
                    completion = output.outputs[0]
                    decision2, payload2 = parse(completion.text, "request", require_separator=args.thinking == "on",
                                                finish_reason=completion.finish_reason, pathway=pathway_of(job["item"]))
                    if decision2 == "REQUEST":
                        decision2 = "REQUEST_AGAIN"
                    row.update(final_decision=decision2, record_after=record, turn2_output=completion.text,
                               turn2_tokens=len(completion.token_ids), turn2_finish_reason=completion.finish_reason,
                               turn2_requested=(payload2 or {}).get("requested"))
            for _, row in rows:
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            print(json.dumps(dict(written=len(done)+min(start+len(batch), len(pending)),
                                  total=len(jobs))), flush=True)


if __name__ == "__main__":
    main()
