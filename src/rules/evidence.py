"""Partial-record gold for a deliberately restricted ABAWD determination.

Not a full SNAP eligibility engine or an agency disposition rule. Age, other
exceptions, prior months and the absence of waivers are fixed in the packet.
All admissible completions are enumerated; missing facts are never defaulted
to false. The existing abawd engine evaluates complete records.
"""
from __future__ import annotations

from itertools import product
from .snap import Household, Member, abawd

LABELS = ("MEETS", "FAILS", "NEEDS_INFO")
FIELDS = ("paid_work_hours", "approved_program_hours", "medical_exemption")


def validate_record(record: dict) -> None:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    if set(FIELDS) - set(record):
        raise ValueError("all legal fields must be present, with null for unknown")
    for field in FIELDS[:2]:
        value = record[field]
        if value is not None and (type(value) is not int or not 0 <= value <= 160):
            raise ValueError(f"{field}: expected integer 0..160 or null")
    value = record["medical_exemption"]
    if value is not None and type(value) is not bool:
        raise ValueError("medical_exemption: expected boolean or null")


def completions(record: dict):
    """Exhaust the stated integer-hour domain, rather than a sampled grid."""
    validate_record(record)
    domains = [
        range(161) if record[f] is None else (record[f],) for f in FIELDS[:2]
    ]
    domains.append((False, True) if record[FIELDS[2]] is None else (record[FIELDS[2]],))
    for paid, program, medical in product(*domains):
        yield dict(paid_work_hours=paid, approved_program_hours=program,
                   medical_exemption=medical)


def complete_label(record: dict) -> str:
    validate_record(record)
    if any(record[f] is None for f in FIELDS):
        raise ValueError("complete_label requires a complete record")
    member = Member(age=35, medically_unfit=record["medical_exemption"],
                    work_hours_month=record["paid_work_hours"] + record["approved_program_hours"],
                    countable_months_used=3)
    return "MEETS" if abawd(member, Household([member]))["eligible_this_month"] else "FAILS"


def resolve(record: dict) -> dict:
    possible = {complete_label(c) for c in completions(record)}
    label = next(iter(possible)) if len(possible) == 1 else "NEEDS_INFO"
    return dict(label=label, possible_labels=sorted(possible),
                unknown_fields=[f for f in FIELDS if record[f] is None])


def minimal_questions(record: dict) -> list[list[str]]:
    """Minimal sets whose verified answers always suffice under this packet."""
    unknown = [f for f in FIELDS if record[f] is None]
    if resolve(record)["label"] != "NEEDS_INFO":
        return []
    answers = []
    for bits in product((False, True), repeat=len(unknown)):
        selected = [f for f, bit in zip(unknown, bits) if bit]
        if not selected or any(set(a).issubset(selected) for a in answers):
            continue
        groups = {}
        for completion in completions(record):
            key = tuple(completion[f] for f in selected)
            groups.setdefault(key, set()).add(complete_label(completion))
        if all(len(labels) == 1 for labels in groups.values()):
            answers.append(selected)
    return sorted(answers, key=lambda a: (len(a), a))
