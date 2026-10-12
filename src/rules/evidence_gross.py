"""Partial-record gold for a deliberately restricted SNAP gross-income test (second rule pathway).

Same evidence semantics as evidence.py: an unknown amount ranges over the stated
whole-dollar domain 0..DOLLAR_MAX; a fact is never defaulted to zero. The label is
computed analytically (min/max gross over the domain) and checked against exhaustive
enumeration in the tests. Household size is always established; no member is elderly
or disabled, so the gross test applies (FY2026 federal limits from snap.py).
"""
from __future__ import annotations

from .snap import FY2026, _by_size

LABELS = ("MEETS", "FAILS", "NEEDS_INFO")
FIELDS = ("earned_income", "unearned_income")
DOLLAR_MAX = 6000


def gross_limit(size: int) -> int:
    return _by_size(FY2026["gross_limit"], FY2026["gross_add"], size)


def validate_record(record: dict) -> None:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    size = record.get("household_size")
    if type(size) is not int or not 1 <= size <= 8:
        raise ValueError("household_size: expected integer 1..8 (always established)")
    if set(FIELDS) - set(record):
        raise ValueError("both income fields must be present, with null for unknown")
    for field in FIELDS:
        value = record[field]
        if value is not None and (type(value) is not int or not 0 <= value <= DOLLAR_MAX):
            raise ValueError(f"{field}: expected integer 0..{DOLLAR_MAX} or null")


def complete_label(record: dict) -> str:
    validate_record(record)
    if any(record[f] is None for f in FIELDS):
        raise ValueError("complete_label requires a complete record")
    return "MEETS" if record["earned_income"] + record["unearned_income"] <= gross_limit(record["household_size"]) else "FAILS"


def resolve(record: dict) -> dict:
    validate_record(record)
    limit = gross_limit(record["household_size"])
    low = sum(0 if record[f] is None else record[f] for f in FIELDS)
    high = sum(DOLLAR_MAX if record[f] is None else record[f] for f in FIELDS)
    possible = set()
    if low <= limit:
        possible.add("MEETS")
    if high > limit:
        possible.add("FAILS")
    label = next(iter(possible)) if len(possible) == 1 else "NEEDS_INFO"
    return dict(label=label, possible_labels=sorted(possible),
                unknown_fields=[f for f in FIELDS if record[f] is None])


def minimal_questions(record: dict) -> list[list[str]]:
    """Under this packet an unresolved gross test is settled only by every unknown amount."""
    unknown = [f for f in FIELDS if record[f] is None]
    if resolve(record)["label"] != "NEEDS_INFO":
        return []
    return [unknown]
