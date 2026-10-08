"""Descriptive paired analysis for the development set, not a confirmatory test."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from rules.evidence import LABELS, resolve


def indicator_bounds(label: str, target: str = "MEETS") -> tuple[float, float]:
    # Invalid/truncated answers are unknown outcomes, never coded as FAILS.
    return (float(label == target),) * 2 if label in LABELS else (0., 1.)


def difference(high: str, low: str) -> tuple[float, float]:
    a, b = indicator_bounds(high), indicator_bounds(low)
    return a[0] - b[1], a[1] - b[0]


def subtract(a, b):
    return a[0] - b[1], a[1] - b[0]


def summarize_effect(by_base: dict, draws: int = 2000, seed: int = 17) -> dict:
    if not by_base:
        return dict(n_bases=0, estimate=None, identification_bounds=None, ci95=None)
    values = np.asarray([np.mean(by_base[b], axis=0) for b in sorted(by_base)])
    lower, upper = values.mean(axis=0)
    identified = bool(np.allclose(values[:, 0], values[:, 1]))
    result = dict(n_bases=len(values), estimate=float(lower) if identified else None,
                  identification_bounds=[float(lower), float(upper)],
                  ci95=None, ci_scope="Conditional on these synthetic base profiles and templates.")
    if len(values) < 3:
        result["ci_reason"] = "Too few base clusters."
    elif np.all(np.ptp(values, axis=0) == 0):
        result["ci_reason"] = "Degenerate empirical variation; do not interpret a zero-width bootstrap as equivalence."
    else:
        rng = np.random.default_rng(seed)
        bootstrap = values[rng.integers(0, len(values), (draws, len(values)))].mean(axis=1)
        result["ci95"] = [float(np.quantile(bootstrap[:, 0], .025)),
                          float(np.quantile(bootstrap[:, 1], .975))]
        result["ci_method"] = "Paired base-cluster percentile bootstrap; worst-case bounds for invalid outputs."
    return result


def rate_bounds(labels: list[str], target: str, correct=None) -> dict:
    if not labels:
        return dict(n=0, estimate=None, bounds=None)
    if correct is None:
        intervals = [indicator_bounds(label, target) for label in labels]
    else:
        intervals = [indicator_bounds(label, gold) for label, gold in zip(labels, correct)]
    lower, upper = np.mean(intervals, axis=0)
    return dict(n=len(labels), estimate=float(lower) if lower == upper else None,
                bounds=[float(lower), float(upper)],
                invalid=sum(label not in LABELS for label in labels))


def score(items: list[dict], outputs: list[dict], allow_partial: bool = False,
          draws: int = 2000) -> dict:
    index = {}
    for item in items:
        if item["item_id"] in index:
            raise ValueError("Duplicate item in dataset")
        if resolve(item["record"])["label"] != item["gold"]:
            raise ValueError("Dataset gold does not match current oracle")
        index[item["item_id"]] = item
    if not outputs:
        raise ValueError("Empty output file")
    data_sha = hashlib.sha256("".join(json.dumps(r, sort_keys=True) + "\n" for r in items).encode()).hexdigest()
    identities = {(r["model"], r.get("revision"), r.get("data_sha256"),
                   r.get("packet_sha256")) for r in outputs}
    if len(identities) != 1:
        raise ValueError("Mixed model, revision, dataset or packet provenance")
    declared_sha = outputs[0].get("data_sha256")
    if declared_sha is not None and declared_sha != data_sha:
        raise ValueError("Output dataset hash mismatch")
    seen = set()
    cells = defaultdict(dict)
    cell_metrics = defaultdict(list)
    extraction = defaultdict(list)
    dimensions = defaultdict(set)
    protocols = defaultdict(set)
    for row in outputs:
        item_id = row["item_id"]
        if item_id not in index:
            raise ValueError("Output refers to an unknown item")
        item = index[item_id]
        key = (item_id, row["method"], row["order"], row["seed"])
        if key in seen:
            raise ValueError("Duplicate output request")
        seen.add(key)
        dimensions[row["method"]].add((row["order"], row["seed"]))
        protocols[row["method"]].add(row.get("protocol_sha256"))
        cell = (row["method"], item["base"], item["condition"],
                item["style"], row["order"], row["seed"])
        cells[cell][item["cue"]] = row["decision"]
        cell_metrics[(row["method"], item["condition"])].append((row["decision"], item["gold"]))
        if row["method"] == "extract_rule":
            parsed = row.get("extracted_record")
            extraction[item["condition"]].append(
                parsed is not None and all(parsed.get(f) == item["record"][f]
                                          for f in ("paid_work_hours", "approved_program_hours", "medical_exemption")))
    if any(len(p) > 1 for p in protocols.values()):
        raise ValueError("Mixed protocols within a method")
    expected = {(i, method, order, seed) for method, ds in dimensions.items()
                for order, seed in ds for i in index}
    missing = expected - seen
    if missing and not allow_partial:
        raise ValueError(f"{len(missing)} requests missing; pass --allow-partial for descriptive smoke summaries")

    effects = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    contrasts = {}
    flips = defaultdict(dict)
    for key, values in cells.items():
        method, base, condition, style, order, seed = key
        if "high" in values and "low" in values:
            d = difference(values["high"], values["low"])
            contrasts[key] = d
            effects[method][f"cue_gap_{condition}"][base].append(d)
            if values["high"] in LABELS and values["low"] in LABELS:
                flips[(method, condition)].setdefault(base, []).append(values["high"] != values["low"])
        if "valence_positive" in values and "valence_negative" in values:
            effects[method][f"valence_gap_{condition}"][base].append(
                difference(values["valence_positive"], values["valence_negative"]))
    for key, material in contrasts.items():
        method, base, condition, style, order, seed = key
        complete_key = (method, base, "complete", style, order, seed)
        if condition == "complete" or complete_key not in contrasts:
            continue
        interaction = subtract(material, contrasts[complete_key])
        effects[method][f"interaction_{condition}_vs_complete"][base].append(interaction)
        a, b = cells[key], cells[complete_key]
        if all(c in a and c in b for c in ("valence_positive", "valence_negative")):
            placebo = subtract(difference(a["valence_positive"], a["valence_negative"]),
                               difference(b["valence_positive"], b["valence_negative"]))
            effects[method][f"valence_adjusted_interaction_{condition}"][base].append(
                subtract(interaction, placebo))
    result = dict(
        stage="development", confirmatory=False, n_items=len(items), n_outputs=len(outputs),
        n_bases=len({i["base"] for i in items}), missing_requests=len(missing),
        effects={method: {name: summarize_effect(v, draws) for name, v in names.items()}
                 for method, names in effects.items()},
        rates={}, paired_flip_rates={},
        caveats=["Development data: no confirmatory p-values or acceptance forecast.",
                 "Repeated renderings, orders and seeds do not increase independent case count.",
                 "Primary interaction uses the same bases; redundant masks exist only in passing profiles.",
                 "Invalid outputs stay missing and receive worst-case outcome bounds.",
                 "Inference does not extend to unseen templates, actual applicants or population harm."],
    )
    for (method, condition), pairs in cell_metrics.items():
        labels, gold = map(list, zip(*pairs))
        metrics = dict(accuracy=rate_bounds(labels, "", correct=gold),
                       meets=rate_bounds(labels, "MEETS"), fails=rate_bounds(labels, "FAILS"),
                       needs_info=rate_bounds(labels, "NEEDS_INFO"))
        if condition == "missing_material":
            needs = metrics["needs_info"]["bounds"]
            metrics["unsupported_definitive_bounds"] = [1-needs[1], 1-needs[0]]
        strata = {label: [l for l, g in pairs if g == label] for label in LABELS}
        per_class = [rate_bounds(v, k)["bounds"] for k, v in strata.items() if v]
        metrics["balanced_accuracy_bounds"] = np.mean(per_class, axis=0).tolist()
        result["rates"].setdefault(method, {})[condition] = metrics
    for (method, condition), bases in flips.items():
        any_flip = [any(events) for events in bases.values()]
        summary = dict(n_bases=len(any_flip), bases_with_any_flip=sum(any_flip),
                       fraction=float(np.mean(any_flip)))
        if not any(any_flip):
            summary["zero_event_one_sided95_upper"] = 1 - .05 ** (1/len(any_flip))
            summary["bound_assumption"] = "IID base-event Bernoulli draws within this design, not unseen-template coverage."
        result["paired_flip_rates"].setdefault(method, {})[condition] = summary
    if extraction:
        result["extraction_exact_record_rate"] = {
            c: dict(n=len(v), exact=float(np.mean(v))) for c, v in extraction.items()}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--allow-partial", action="store_true")
    p.add_argument("--draws", type=int, default=2000)
    args = p.parse_args()
    load = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    result = score(load(args.data), load(args.results), args.allow_partial, args.draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(n_outputs=result["n_outputs"], missing=result["missing_requests"],
                         confirmatory=False, out=str(args.out)), indent=2))


if __name__ == "__main__":
    main()
