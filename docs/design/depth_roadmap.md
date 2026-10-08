# Depth roadmap for Design D (draft, 2026-10-08; assistant for the PI, pending approval)

The development set (docs/design/design_D_evidence.md) is the right floor: gold is computable, the pairing is clean, invalid
outputs are bounded. It is also the easiest possible version of the task, and its own audit says so: the note is labelled
UNVERIFIED, the packet says notes certify nothing, the missing field literally reads UNKNOWN, the rule is one line
(medical OR hours >= 80), and 24 bases are 3 logical profiles x 8 numbers. A competent reasoning model will very likely
answer NEEDS_INFO everywhere, and a null on this floor is not a paper. Depth comes from building the gradient on which the
effect can appear and showing where along it the boundary lies. Each item below says what it adds, why, and what it costs.

## 1. Cue-surface ladder (primary manipulation of "how explicit is the cue")
| level | surface | status |
| --- | --- | --- |
| S0 | labelled UNVERIFIED CHARACTER NOTE, opinion words (lazy / hardworking) | implemented (development set) |
| S1 | same opinion inside the caseworker narrative, no label, no instruction that notes certify nothing | to build |
| S2 | behavioural facts with the same deservingness meaning, legally immaterial under the packet: "attended every scheduled appointment / missed two scheduled appointments", "submitted the form the same day / three weeks late" | to build; the deployment-realistic surface |
Why: explicit labels make resistance easy (Shafiei et al. 2026 "performative compliance"; Karvonen & Marks 2025: anti-bias
instructions fail once realistic context is added). Pre-register S2 as the primary surface and S0 as the floor; report the
whole ladder. Cost: two more template sets, author audit of parallelism, no new oracle.

## 2. Evidence ladder (primary manipulation of "how tempting is the gap")
| level | record state | gold |
| --- | --- | --- |
| E0 | field printed as UNKNOWN | NEEDS_INFO (implemented) |
| E1 | field absent (line not printed) | NEEDS_INFO |
| E2 | self-reported, unverified ("applicant states 48 program hours; no attendance record on file") | NEEDS_INFO under the packet's verification rule |
| E3 | partially verified ("attendance records cover 2 of 4 weeks: 24 hours") | NEEDS_INFO |
| E4 | conflicting sources ("provider letter: 32 hours; applicant: 48 hours") | NEEDS_INFO |
Why: H2 of the study becomes a trend: the cue-by-missingness interaction grows with temptation. Gold stays computable
(the oracle treats unverified values as unknown; add a `verified` flag per field). Cost: oracle extension + tests, packet
rule for what counts as established, one template per level.

## 3. Second rule pathway (generality inside the same question)
Gross-income test with an income component missing (unearned income not established) using src/rules/snap.py, and the
exemption chain with the child's age missing. Same three missingness arms, same cues. Why: the audit's main-study gate
names it; one-line rules invite "trivial task". Cost: low (engine exists); oracle needs a completion domain for dollars
(use the packet's stated range) and the irrelevant-field control for each pathway.

## 4. Base diversity (the cluster unit must carry real variation)
Bases from SNAP QC household structures (names, ages, household composition, rent/utilities) as in the hub's
make_rules_pilot.py, 40+ bases, two independently authored template sets per rendering. Why: 24 bases that are 3 profiles
x 8 numbers overstate independence; reviewers will count 3. Cost: generator change, QC file (not redistributed; in the hub).

## 5. Readout ladder
Thinking on, 2 seeds (primary); same prompt thinking off; first-token excluded (hub result: it cannot measure a judgment
the model does not compute). Qwen3 8B / 14B / 32B-AWQ, gpt-oss-20b (second family), Llama-3.3-70B-AWQ adapter if it fits;
2 frontier models on the core cells after the pre-registered gate.

## 6. Verbalization coding
When the note moves the decision, does the trace cite it? Cells: {decision moved / not} x {trace cites note / not}.
Regex pass + LLM judge validated on 300 hand-coded traces (report agreement). Why: "silent gap-filling" vs "openly cited
opinion" are different failures and both are reportable; decision memos are the deployment surface.

## 7. Consequence analysis
Apply each model to a QC-weighted synthetic caseload with a stated share of incomplete records. Report unsupported definitive
decisions per 100k and verification requests per 100k by cue group. The second quantity is the administrative-burden
measure (Herd & Moynihan) and is what a CSS reviewer will call the contribution.

## 8. Optional, if time: relevance switch
A pathway where the reason for leaving work IS material (voluntary quit / good cause, 7 CFR 273.7(i)-(j)) with the same cue
text. Tests "uses the cue exactly where the law says". Needs a careful legal audit; a Paper 3 candidate otherwise.

## Order of work
1. Run the development set as the runbook says (smoke 22 -> competence 352 -> paired 3,520 on Qwen3-8B, then 14B).
   Read 30 CoTs per model before scoring. Expect S0/E0 to be near NEEDS_INFO ceiling for 14B.
2. Build S1/S2 and E1-E4 generators and oracle extension; tests first; synthetic-data validation of the scorer's interaction.
3. Pilot the ladders on 10 bases, 8B and 14B. Gate: decision defined in the CoTs; NEEDS_INFO rate at the neutral cue between
   0.2 and 0.9 in at least two ladder cells (otherwise there is no boundary to measure).
4. Freeze (OSF pre-registration): surfaces, evidence levels, pathway set, bases, models, seeds, orders, MDE, exclusions,
   multiplicity, reporting. Then the main run, frontier models, coding, consequence analysis, writing.

## Known limits of the current development set (to state in the paper if kept as the floor)
Single legal condition with one disjunction; cues are opinion words from third parties; the packet instructs the model
how to treat the note; forward/reverse orders keep FAILS in the middle; 3 logical profiles; no PolicyEngine cross-check of
the partial-record oracle (it is checked against a hand-written truth table instead).
