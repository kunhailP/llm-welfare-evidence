#!/bin/bash
# Post queue (2026-10-12, pre-registered in docs/design/design_D_ladder.md, "Packet ablation and second family"):
# (1) packet ablation on the ABAWD S2 missing-material cells (norule / emph) for qwen3-8b and qwen3-14b;
# (2) gpt-oss-20b (second open family) on the ladder S2 cells: plain on missing_material + complete, request on E1/E2.
set -u
source /workspace/logs/env.sh
cd "$(dirname "$0")/../../.."
PY=/workspace/venv_evidence/bin/python
OUT=results/evidence_ladder; mkdir -p $OUT
run () {  # out-name, args...
  local name=$1; shift
  if [ -f $OUT/$name.jsonl ]; then RESUME=--resume; else RESUME=; fi
  echo "=== $name $(date)"
  $PY src/run/run_evidence_pilot.py --max-num-seqs 128 --batch-size 512 $RESUME --out $OUT/$name.jsonl "$@" || echo "FAILED $name"
}
for M in qwen3-8b qwen3-14b; do
  for V in norule emph; do
    run ${M}_ablation_${V} --model $M --data data/evidence_ladder_${V}/dev.jsonl --packet configs/evidence_packet_ladder_${V}.md \
        --filter "condition=missing_material" --seeds 0,1 --orders forward,reverse
  done
done
export HF_HOME=/root/hf_local   # gpt-oss-20b lives on the local disk (network volume quota reached, 2026-10-12)
run gpt-oss-20b_plain --model gpt-oss-20b --data data/evidence_ladder/dev.jsonl \
    --filter "surface=S2,condition=complete|missing_material|missing_irrelevant|missing_redundant" --seeds 0,1 --orders forward,reverse
run gpt-oss-20b_request_e12 --model gpt-oss-20b --data data/evidence_ladder/dev.jsonl --method request \
    --filter "surface=S2,condition=missing_material,evidence=E1|E2" --seeds 0,1 --orders forward,reverse
echo "=== post queue done $(date)"
