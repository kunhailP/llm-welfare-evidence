# North star (this repo; carried over from the hub on 2026-10-08)

## Standing policies (PI)
- **Bar:** main-conference quality, ARR overall ~4.0-4.5. "Depth first": one problem, dug deeply.
- **Venue:** the PI's stated intent is NAACL quality for the preliminary work and ACL 2027 (ARR January 2027) for the
  follow-up. NAACL 2027's last eligible ARR cycle closes 2026-10-12 AoE; no GPU result of Design D exists, so this repo's
  study is on the January track unless the PI decides otherwise and logs it.
- **Two questions for every step:** novelty (what prior work does not show) and venue fit (which reviewer would call it a
  clear NLP contribution). If a step serves neither, drop it.
- **No human-participant baseline. No paid API models until the design is frozen** (then 2 frontier models on the core cells;
  disclose the Maryland/Anthropic conflict of interest if Claude is one of them).
- **Read results one by one; read CoTs before scoring; pre-register before reading.**
- **Git:** commits authored by the PI only, no AI co-author trailers; never store access tokens.
- **Tracks:** computational social science primary; evaluation methods, ethics/fairness secondary.

## What the hub already established (do not re-run; cite)
- Rule-computable determinations with reasoning: verdicts at ceiling, paired deservingness contrasts 0 (Qwen3 8B/14B/32B).
- Direct first-token verdicts on aggregated facts follow a prior; any added sentence moves them; the polarity flip exposes a
  yes-bias. First-token readouts cannot measure a judgment the model does not compute.
- Design C (open hardship standard) had no gold and an undefined decision; that is why this study uses evidence sufficiency,
  where NEEDS_INFO is computable.

## Where the novelty must come from
Not "LLMs are sensitive to positive/negative wording" and not "LLMs ask for clarification under underspecification"
(ShARC). The claim is conditional: a legally irrelevant moral description changes the decision **specifically when a
decisive fact is missing**, relative to complete and irrelevant-missing records and relative to a non-moral valence
control, measured against an executable partial-record gold. See docs/design/depth_roadmap.md for what makes it deep.
