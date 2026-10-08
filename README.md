# LLM welfare evidence: do work-ethic cues fill gaps in the record?

When a fact that a welfare rule needs is missing from the case file, does an unverified description of the applicant's
work ethic push an LLM's determination toward a definitive answer (MEETS / FAILS) instead of NEEDS_INFO? This repo holds
Design D: the partial-record oracle, the development generator, the resumable runner, the paired scorer, and the plan to
take it from pilot to a main study.

Companion repo: https://github.com/kunhailP/llm-welfare-discretion (the hub: SNAP rules-as-code testbed, Design B
results, Design C audit, stage-1 history). That repo is the record for Paper 1; this one is Paper 2.
Split on 2026-10-08 so that this study starts clean, with the standing policies carried over (docs/NORTH_STAR.md).

## Status (2026-10-08)
Development protocol implemented and CPU-checked (docs/results/design_D_cpu_checks.md). First GPU runs on Qwen3-8B
(docs/results/design_D_gpu_pilot.md): smoke 22/22, competence gate passed, missing-material NEEDS_INFO at 1.000 with the neutral
note, so the current floor has no headroom. No cue finding is claimed. **Start with docs/design/design_D_evidence.md, then docs/design/depth_roadmap.md,
then docs/RUNPOD_EVIDENCE_PILOT.md.**

## Layout
    configs/      evidence_packet.md (the rule packet shown to the model), models.yaml (pinned revisions), requirements.lock.txt
    src/rules/    snap.py (complete-record ABAWD engine, from the hub), evidence.py (partial-record oracle: exhaustive completions)
    src/gen/      make_evidence_pilot.py (24 bases -> 880 development items, manifest with hashes)
    src/run/      run_evidence_pilot.py (vLLM, resumable, provenance), download_evidence_models.py
    src/eval/     score_evidence_pilot.py (paired contrasts, interaction, base-cluster bootstrap, invalid-output bounds)
    tests/        test_evidence_pilot.py (20: oracle truth table, pairing, scorer failure handling), test_snap_rules.py (9)
    docs/         NORTH_STAR, decisions (log), design/ (design_D_evidence, design_D_audit, depth_roadmap), results/, RUNPOD runbook
    data/         external/snap_params (FNS FY2026 PDFs, gold for snap.py); evidence_pilot/ is generated and not tracked
    lit/          literature notes copied from the hub (verification conventions inside each file)

## Checks (CPU, no model)
    python -m unittest discover -s tests -p test_evidence_pilot.py -v
    pytest -q tests/test_snap_rules.py
    python src/gen/make_evidence_pilot.py --bases 24 --seed 11
    python src/run/run_evidence_pilot.py --model qwen3-8b --cue neutral --base-limit 3 --orders forward --dry-run --out /tmp/unused.jsonl

## Environment (L40 pod)
    python3.12 -m venv /workspace/venv && /workspace/venv/bin/pip install -r configs/requirements.lock.txt
    export HF_HOME=/workspace/hf
    python src/run/download_evidence_models.py --model qwen3-8b
Then follow docs/RUNPOD_EVIDENCE_PILOT.md: 22-request neutral smoke, 352-request competence run, 3,520-request paired run.

## Working rules (carried over from the hub)
- Every design decision is logged in docs/decisions.md with its reason; commits are authored by the PI only.
- Pre-register hypotheses and fallback rules before reading results; no task changes to chase an effect.
- Look at each result before running the next; read model reasoning before scoring it.
- Open models only until the design is frozen; no human-participant baseline.
