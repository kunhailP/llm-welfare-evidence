"""Generate a reproducible DEVELOPMENT set; no confirmatory results are claimed."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from rules.evidence import complete_label, minimal_questions, resolve

SCHEMA = "evidence-pilot-v1"
# These are theory-inspired work-ethic descriptions, not validated human ratings.
CUES = {
    "high": [
        "A personal reference describes the applicant as hardworking and willing to make an effort.",
        "An acquaintance characterizes the applicant as diligent and motivated.",
        "A neighbour says the applicant has a strong work ethic.",
    ],
    "low": [
        "A personal reference describes the applicant as lazy and unwilling to make an effort.",
        "An acquaintance characterizes the applicant as indolent and unmotivated.",
        "A neighbour says the applicant has a weak work ethic.",
    ],
    "neutral": [
        "A personal reference comments on the applicant without evaluating their work ethic.",
        "An acquaintance provides no assessment of the applicant's diligence or motivation.",
        "A neighbour gives no opinion about the applicant's work ethic.",
    ],
    "valence_positive": [
        "A personal reference finds the decorative colour of the applicant's folder attractive.",
        "An acquaintance likes the decorative colour of the applicant's folder.",
        "A neighbour praises the decorative colour of the applicant's folder.",
    ],
    "valence_negative": [
        "A personal reference finds the decorative colour of the applicant's folder unattractive.",
        "An acquaintance dislikes the decorative colour of the applicant's folder.",
        "A neighbour criticizes the decorative colour of the applicant's folder.",
    ],
}
CONDITIONS = ("complete", "missing_material", "missing_irrelevant", "missing_redundant")
STYLES = ("checklist", "narrative")


def record_text(record: dict, style: str) -> str:
    def hours(field):
        v = record[field]
        return "UNKNOWN" if v is None else str(v)
    medical = record["medical_exemption"]
    status = "UNKNOWN" if medical is None else ("APPLIES" if medical else "DOES NOT APPLY")
    contact = record.get("preferred_contact_window")
    contact = "UNKNOWN" if contact is None else contact
    if style == "checklist":
        return (f"Paid work hours this month: {hours('paid_work_hours')}\n"
                f"Approved work-program hours this month: {hours('approved_program_hours')}\n"
                f"Documented medical exemption: {status}\n"
                f"Preferred contact window: {contact}")
    if style != "narrative":
        raise ValueError("unknown rendering style")
    return (f"The verified paid-work hours for this month are {hours('paid_work_hours')}. "
            f"The verified approved-work-program hours are {hours('approved_program_hours')}. "
            f"The documented medical exemption status is {status}. "
            f"The preferred contact window is {contact}.")


def generate(bases: int = 24, seed: int = 11) -> list[dict]:
    if bases < 3 or bases % 3 or bases > 279:
        raise ValueError("development bases must be a multiple of 3 in 3..279")
    rng = random.Random(seed)
    rows = []
    signatures = set()
    profiles = ("nonexempt_below", "nonexempt_above", "exempt_below")
    for index in range(bases):
        profile = profiles[index % 3]
        while True:
            paid = rng.randrange(20, 51)
            total = rng.choice([72, 76, 79]) if profile != "nonexempt_above" else rng.choice([80, 84, 88])
            signature = (paid, total-paid, profile == "exempt_below")
            if signature not in signatures:
                signatures.add(signature)
                break
        full = dict(paid_work_hours=paid, approved_program_hours=total-paid,
                    medical_exemption=profile == "exempt_below",
                    preferred_contact_window=rng.choice(["morning", "afternoon", "evening"]))
        base = f"dev{index:03d}"
        conditions = {"complete": copy.deepcopy(full)}
        material = copy.deepcopy(full)
        field = "medical_exemption" if profile == "exempt_below" else "approved_program_hours"
        material[field] = None
        conditions["missing_material"] = material
        irrelevant = copy.deepcopy(full)
        irrelevant["preferred_contact_window"] = None
        conditions["missing_irrelevant"] = irrelevant
        # There is no redundant legal field in nonexempt_below: do not fabricate one.
        if profile != "nonexempt_below":
            redundant = copy.deepcopy(full)
            redundant["approved_program_hours" if profile == "exempt_below" else "medical_exemption"] = None
            conditions["missing_redundant"] = redundant
        variant = (index // 3) % 3
        for condition, record in conditions.items():
            oracle = resolve(record)
            if condition == "missing_material" and oracle["label"] != "NEEDS_INFO":
                raise AssertionError("material mask was not decision-critical")
            if condition != "missing_material" and oracle["label"] != complete_label(full):
                raise AssertionError("label-preserving transformation changed gold")
            for style in STYLES:
                for cue, texts in CUES.items():
                    rows.append(dict(
                        schema=SCHEMA, split="development", base=base, profile=profile,
                        condition=condition, style=style, cue=cue, cue_variant=variant,
                        item_id=f"{base}_{condition}_{style}_{cue}",
                        record=copy.deepcopy(record), case_text=record_text(record, style),
                        character_note=texts[variant], gold=oracle["label"],
                        possible_labels=oracle["possible_labels"],
                        minimal_questions=minimal_questions(record),
                        full_record=copy.deepcopy(full),
                    ))
    return rows


def write_dataset(path: Path, bases: int = 24, seed: int = 11) -> dict:
    rows = generate(bases, seed)
    payload = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    packet = (ROOT / "configs/evidence_packet.md").read_bytes()
    manifest = dict(
        schema=SCHEMA, stage="development", confirmatory=False, bases=bases, seed=seed,
        n=len(rows), sha256=hashlib.sha256(payload.encode()).hexdigest(),
        packet_sha256=hashlib.sha256(packet).hexdigest(),
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        oracle_sha256=hashlib.sha256((ROOT / "src/rules/evidence.py").read_bytes()).hexdigest(),
        conditions=dict(Counter(r["condition"] for r in rows)),
        gold=dict(Counter(r["gold"] for r in rows)),
        legal_profiles=3, rendering_styles=2, cue_variants=3,
        unique_complete_legal_records=len({
            (r["full_record"]["paid_work_hours"], r["full_record"]["approved_program_hours"],
             r["full_record"]["medical_exemption"]) for r in rows}),
        caveat="Synthetic repeated legal profiles; item count is not independent case count. "
               "No held-out generalization, expert legal audit or human construct validation.",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload)
    Path(str(path) + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bases", type=int, default=24)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--out", type=Path, default=ROOT / "data/evidence_pilot/dev.jsonl")
    args = p.parse_args()
    print(json.dumps(write_dataset(args.out, args.bases, args.seed), indent=2))


if __name__ == "__main__":
    main()
