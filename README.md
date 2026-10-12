# LLM welfare evidence: do work-ethic cues fill gaps in the record?

When a fact that a welfare rule needs is missing from the case file, does an unverified description of the applicant's
work ethic push an LLM's determination toward a definitive answer (MEETS / FAILS) instead of NEEDS_INFO? This repo holds
Design D: the partial-record oracle, the development generator, the resumable runner, the paired scorer, and the plan to
take it from pilot to a main study.

Companion repo: https://github.com/kunhailP/llm-welfare-discretion (the hub: SNAP rules-as-code testbed, Design B
results, Design C audit, stage-1 history). That repo is the record for Paper 1; this one is Paper 2.
Split on 2026-10-08 so that this study starts clean, with the standing policies carried over (docs/NORTH_STAR.md).

## Status (2026-10-12): ladder run on Qwen3-8B and GPT-5; 14B and the E1/E2 request protocol in the queue
After the external review of 2026-10-12 (summarised in docs/decisions.md): cue-surface ladder S0/S1/S2, evidence ladder E0/E1/E2,
restoration arms, a second rule pathway (gross-income test) and a one-step clarification protocol (`--method request`) are
implemented with reading rules fixed before any run (docs/design/design_D_ladder.md). Findings so far (docs/results/design_D_ladder_pilot.md):
work-ethic cues move no determination on any surface, evidence state or model; what moves them is how the missing fact is
presented: Qwen3-8B turns an absent or self-reported fact into an established zero (NEEDS_INFO 0.88-1.00 at E0, 0.44-0.69
when the line is absent, 0.06-0.29 when the applicant's statement is on file; the premature decisions are denials on the work
requirement and passes on the income test); GPT-5 keeps the error only for the undocumented exemption claim. Two mitigations
work at 8B: the one-step REQUEST protocol (names exactly the pivotal field, 100 % correct after verification) and
null-preserving extraction with the rule oracle (0.92-1.00 at E2). A legal reviewer upheld the gold labels
(docs/design/legal_review_response_2026-10-12.md). Read traces first: `python src/eval/read_traces.py ...` (rule R7).

## Status (2026-10-08)
Development protocol implemented and CPU-checked (docs/results/design_D_cpu_checks.md). First GPU runs on Qwen3-8B
(docs/results/design_D_gpu_pilot.md): smoke 22/22, competence gate passed, missing-material NEEDS_INFO at 1.000 with the neutral
note, so the current floor has no headroom. No cue finding is claimed. **Start with docs/design/design_D_evidence.md, then docs/design/depth_roadmap.md,
then docs/RUNPOD_EVIDENCE_PILOT.md.**

## Layout
    configs/      evidence_packet.md (first set), evidence_packet_ladder.md (ABAWD ladder), evidence_packet_gross.md (gross test), models.yaml, requirements.lock.txt
    src/rules/    snap.py (complete-record engine, from the hub), evidence.py (ABAWD partial-record oracle), evidence_gross.py (gross-test partial-record oracle)
    src/gen/      make_evidence_pilot.py (first set, 880 items), make_evidence_ladder.py (ladder, 2,340 items: surfaces x evidence states x conditions x pathways)
    src/run/      run_evidence_pilot.py (vLLM; methods plain / fact_table / extract_rule / request), run_evidence_api.py (OpenAI / Anthropic), queues/, download_evidence_models.py
    src/eval/     score_evidence_pilot.py (first set), score_evidence_ladder.py (composition, premature vs over-verification, contrasts, restoration, extraction, request metrics, trace mentions), read_traces.py (rule R7)
    tests/        test_evidence_pilot.py (20), test_evidence_ladder.py (14), test_snap_rules.py (9)
    docs/         NORTH_STAR, decisions (log), design/ (design_D_evidence, design_D_audit, depth_roadmap), results/, RUNPOD runbook
    data/         external/snap_params (FNS FY2026 PDFs, gold for snap.py); evidence_pilot/ and evidence_ladder/ are generated (manifests with hashes)
    lit/          literature notes copied from the hub (verification conventions inside each file)

## Checks (CPU, no model)
    python -m unittest discover -s tests -p test_evidence_pilot.py -v
    python -m unittest tests/test_evidence_ladder.py -v
    python src/gen/make_evidence_ladder.py --bases 12
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
