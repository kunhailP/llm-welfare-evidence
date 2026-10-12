#!/bin/bash
# Ladder queue L2-L5 (2026-10-12), one L40. Usage: bash src/run/queues/run_ladder_queue.sh <model-id>
# Pre-registered reading rules: docs/design/design_D_ladder.md. Every run is resumable (--resume).
set -u
MODEL=${1:-qwen3-8b}
source /workspace/logs/env.sh
cd "$(dirname "$0")/../../.."
PY=/workspace/venv_evidence/bin/python
DATA=data/evidence_ladder/dev.jsonl
OUT=results/evidence_ladder
mkdir -p $OUT
run () {  # name, extra args...
  local name=$1; shift
  if [ -f $OUT/${MODEL}_$name.jsonl ]; then RESUME=--resume; else RESUME=; fi
  echo "=== $name $(date)"
  $PY src/run/run_evidence_pilot.py --model $MODEL --data $DATA --out $OUT/${MODEL}_$name.jsonl \
      --max-num-seqs 128 --batch-size 512 $RESUME "$@" || { echo "FAILED $name"; return 1; }
}
# L2: plain, all cells, two seeds, both orders
run plain --seeds 0,1 --orders forward,reverse
# L3: request protocol on the core cells, both pathways, two seeds, both orders
run request --method request --seeds 0,1 --orders forward,reverse \
    --filter "evidence=E0,condition=complete|missing_material|missing_irrelevant|missing_redundant"
# L4: extraction diagnostic on S2, every condition, forward order, two seeds
run extract --method extract_rule --seeds 0,1 --orders forward --filter "surface=S2"
echo "=== queue done $(date)"
# L3b (appended 2026-10-12 after reading L3): the request protocol on the cells where the error lives, E1/E2, all surfaces.
run request_e12 --method request --seeds 0,1 --orders forward,reverse \
    --filter "condition=missing_material,evidence=E1|E2"
echo "=== queue (with L3b) done $(date)"
