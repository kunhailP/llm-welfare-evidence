# Design D: first GPU runs, Qwen3-8B thinking on (2026-10-08, L40; development data, not confirmatory)

Runner src/run/run_evidence_pilot.py (vLLM 0.30.0, pinned revision, T=0.6/top_p 0.95/top_k 20, 4,096 new tokens, seed 0).
Raw outputs: results/evidence_pilot/ (not tracked); scores: qwen3-8b_neutral_score.json.

## Smoke (22 requests, 3 bases, neutral note, forward order)
22/22 correct, all finish_reason = stop, 328-982 output tokens. NEEDS_INFO produced on every missing-material item.

## Competence (352 requests, 24 bases, neutral note, forward + reverse order)
| condition | accuracy bounds | balanced accuracy | NEEDS_INFO rate | invalid |
| --- | --- | --- | --- | --- |
| complete | 0.990-1.000 | 0.984-1.000 | 0.000-0.010 | 1 |
| missing material | 1.000 | 1.000 | 1.000 | 0 |
| missing irrelevant | 1.000 | 1.000 | 0.000 | 0 |
| missing redundant | 0.953-0.969 | 0.953-0.969 | 0.031-0.047 | 1 |
Decisions: MEETS 189, NEEDS_INFO 98, FAILS 63, INVALID 2; mean 510 output tokens; forward and reverse orders agree in composition.

## Reading
- The development gate (>= 95 % valid, >= 90 % balanced accuracy on complete / irrelevant / redundant) is passed at 8B.
- The explicit-UNKNOWN, labelled-note floor (S0/E0 in docs/design/depth_roadmap.md) is at ceiling for the smallest model with the
  neutral note. The paired cue run can still show an interaction, but there is no headroom in NEEDS_INFO on missing-material items
  (1.000), so a null there is expected and uninformative. The ladders (S1/S2 surfaces, E1-E4 evidence states) are needed before
  any main-study claim.
- Unnecessary NEEDS_INFO on redundant masks (3-5 %) is the one competence slack worth watching in the paired run.
