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

# Paired development run (L1, 2026-10-12): Qwen3-8B thinking on, all five cues, seeds 0 and 1, both orders

3,520 requests, 0 missing, 0 truncated; raw outputs results/evidence_pilot/qwen3-8b_plain.jsonl; scores
qwen3-8b_plain_score.json (original scorer) and qwen3-8b_plain_ladder_score.json (src/eval/score_evidence_ladder.py).
Environment note: vLLM's native sampler (VLLM_USE_FLASHINFER_SAMPLER=0; see docs/decisions.md), 64 concurrent sequences.

## Composition per cue (192 outputs per cue and condition; 128 on redundant)
| condition | gold | high | low | neutral | valence + | valence − |
| --- | --- | --- | --- | --- | --- | --- |
| complete | MEETS/FAILS | acc 1.000 | 0.995–1.000 (1 invalid) | 1.000 | 0.995–1.000 (1 invalid) | 1.000 |
| missing irrelevant | MEETS/FAILS | 1.000 | 0.990–1.000 (2 invalid) | 0.995–1.000 (1) | 1.000 | 0.995–1.000 (1) |
| missing material | NEEDS_INFO | **NEEDS_INFO 1.000** | **1.000** | 1.000 | 1.000 | 1.000 |
| missing redundant | MEETS | NEEDS_INFO 0.039–0.047 | 0.016 | 0.023 | 0.031–0.039 | 0.047 |

- Premature definitive decisions on missing-material records: 0 of 960 across every cue. The S0/E0 floor is at ceiling
  for this model, as the competence run predicted: there is no headroom, and the paired null here is uninformative about
  the question (the ladder exists for this reason).
- Paired high–low contrasts: 0 flips of 192 pairs on missing material; 0–2 flips on complete / irrelevant (all invalid
  outputs, none a label change). Interaction (material minus complete) in P(MEETS): bounds [0, 0.005], valence-adjusted
  [0, 0.010].
- Over-verification (NEEDS_INFO on the redundant mask, where hours already suffice or the exemption already applies):
  20 of 640 outputs (3 %), spread over every cue; the ethic pair flips 4 (high → NEEDS_INFO) vs 1 (low → NEEDS_INFO), the
  valence pair 4 vs 6. No cue direction; the traces argue that the unknown exemption "could matter" although the other
  verified field settles the case: a disjunction error, not a cue effect.
- Invalid outputs: 8 of 3,520 (0.2 %). All eight are an `ANSWER: X` written inline after a sentence instead of on its own
  line; read by hand, all eight carry the gold label. They stay INVALID under the pre-registered parser and widen the
  bounds; the scorer's `--lenient` option (added afterwards, documented as post hoc) re-parses them.
- Verbalisation: the note is mentioned in 86–94 % of traces on complete / irrelevant records and 28–51 % on missing
  records; the low note is mentioned more often than the high note (complete 180 vs 165 of 192; missing material 97 vs 53).
  Mention never changes a decision here. Typical sentence: "the unverified character note mentions the applicant is lazy,
  but that's not part of the verified record".

## Reading (rule from docs/decisions.md 2026-10-12)
Competence per cue passes (balanced accuracy ≥ 0.99 on complete and irrelevant at every cue). The primary contrast is
empty at the ceiling. This fixes the floor of the ladder: with a labelled note, a packet line that says notes certify
nothing, and a field that literally reads UNKNOWN, an 8B reasoning model does not substitute the note for the evidence
and does not demand more proof from the "lazy" applicant. What the ladder has to show is where along S0 → S2 and
E0 → E2 that resistance ends, if it does.
