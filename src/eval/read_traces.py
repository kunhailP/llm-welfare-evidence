"""Rule R7 helper: print a stratified sample of raw outputs (trace + final answer) with gold, so that traces are
read before scores are interpreted. Usage:
  python src/eval/read_traces.py --data data/evidence_ladder/dev.jsonl --results results/evidence_ladder/qwen3-8b_plain.jsonl \
      --per-cell 2 --filter condition=missing_material --out /tmp/traces.md
Prints a Markdown file; never changes any result."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--per-cell", type=int, default=2)
    p.add_argument("--filter", default="")
    p.add_argument("--only-wrong", action="store_true", help="only outputs whose decision differs from gold")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-chars", type=int, default=6000)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    items = {r["item_id"]: r for r in map(json.loads, a.data.read_text().splitlines()) if r}
    filters = {}
    for part in filter(None, a.filter.split(",")):
        k, _, v = part.partition("=")
        filters[k] = set(v.split("|"))
    cells = defaultdict(list)
    for line in a.results.read_text().splitlines():
        r = json.loads(line)
        it = items[r["item_id"]]
        if any(str(it.get(k)) not in v for k, v in filters.items()):
            continue
        if a.only_wrong and r["decision"] == it["gold"]:
            continue
        key = (it.get("pathway", "abawd"), it.get("surface", "S0"), it.get("evidence", "E0"), it["condition"], it["cue"])
        cells[key].append((it, r))
    rng = random.Random(a.seed)
    out = []
    for key in sorted(cells):
        sample = rng.sample(cells[key], min(a.per_cell, len(cells[key])))
        for it, r in sample:
            out.append(f"## {'|'.join(key)}  item={it['item_id']} order={r['order']} seed={r['seed']}\n"
                       f"**gold {it['gold']} / decision {r['decision']}"
                       + (f" / requested {r.get('requested_fields')} / final {r.get('final_decision')}" if r.get('method') == 'request' else "")
                       + f"** ({r.get('output_tokens')} tokens, finish {r.get('finish_reason')})\n\n"
                       f"> {it['case_text']}\n> NOTE: {it.get('character_note')}\n\n```\n{r['output'][:a.max_chars]}\n```\n"
                       + (f"\nTURN 2:\n```\n{(r.get('turn2_output') or '')[:a.max_chars]}\n```\n" if r.get('turn2_output') else ""))
    a.out.write_text("\n".join(out))
    print(f"{sum(len(v) for v in cells.values())} outputs in {len(cells)} cells; wrote {a.out}")


if __name__ == "__main__":
    main()
