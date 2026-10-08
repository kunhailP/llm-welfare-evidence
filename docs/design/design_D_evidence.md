# Design D: evidence sufficiency and work-ethic cues

2026-10-08. Status: IMPLEMENTED DEVELOPMENT PROTOCOL, NOT A PREREGISTERED MAIN STUDY.
No model results from this design exist yet. The previous Design C audit remains
part of the research record. Repository snapshot used: 881576e3337845e00ad127b7b4052fe51ac5b244.

## Question and claim boundary

Do work-ethic descriptions affect LLM welfare-rule determinations particularly
when a legally decisive fact is missing?

Candidate result, not an established finding: information insufficiency allows
an unverified moral description to act as a substitute for legally necessary
evidence. A contrast in output does not prove an internal psychological mechanism.

This is a study of a restricted welfare eligibility condition under incomplete
evidence. It is not a study of administrative discretion, material need, benefit
allocation preferences, actual caseworkers or actual deployment. A missing fact
is not a discretionary standard. The task does not ask whether the person
deserves assistance or whether an agency should grant an exemption.

Political relevance: the experiment holds the verified legal record fixed while
changing the moral description. Different categorical determinations would
undermine equal treatment of equivalent evidence. This is a procedural concern;
we do not infer demographic discrimination or real-world harm from synthetic
cases.

## Why this could constitute an NLP contribution

The contribution must identify a specific conditional failure in combining
natural-language rules with partial records, rather than merely show sensitivity
to positive/negative wording. It combines a counterfactual measurement protocol,
an executable partial-information oracle, and controlled diagnostics.

| Prior work | Already established | What this study must add |
|---|---|---|
| ShARC, Saeidi et al. 2018 | Rules plus underspecified scenarios require clarification | A moral-cue interaction with decision-critical missing evidence |
| LexGuard, Chen et al. 2026 | Legal changes should alter decisions; irrelevant changes should not; solver grounding | Sufficiency of partial evidence and contrasts against irrelevant and redundant missingness |
| FairFund-Bench, Lukk 2026 | Deservingness framings affect financial-assistance allocation | Rule-bound determinations with independently checkable labels and fixed legal records |
| Does Thinking Help Fairness?, Pan et al. 2026 | Thinking/non-thinking fairness differences | Within-protocol evidence conditions; no claim that thinking itself eliminates bias |

The 2026 comparisons above are initially based on primary abstracts and the
existing literature notes. Full-text overlap checks are required before claiming
novelty in the final paper. A welfare domain, three labels, a rule engine or a
reasoning model alone is not novelty.

Sources:
- https://aclanthology.org/D18-1233/
- https://arxiv.org/abs/2605.26530
- https://arxiv.org/abs/2607.28934
- https://arxiv.org/abs/2609.30768

## Restricted legal task and gold

The packet fixes age 35, three previously used countable months, no other
exemptions, waivers or good-cause routes. Paid-work hours, approved-program hours
and documented medical exemption status are the only variable legal fields.

For a complete record, the adult satisfies the selected condition if a medical
exemption applies or paid hours plus approved-program hours are at least 80.
Complete records are evaluated by the existing SNAP ABAWD engine.

For a partial record, enumerate every admissible completion. Unknown hour fields
range over the integer domain 0..160 and an unknown medical status over both
booleans. These are experimental completion domains, not empirical priors.

- All completions pass: MEETS.
- All completions fail: FAILS.
- Passing and failing completions both exist: NEEDS_INFO.

NEEDS_INFO is an experimental label. It does not encode actual agency procedures
for pending, denial, verification deadlines or continued benefits. MEETS does not
mean overall SNAP approval. The existing PolicyEngine cross-check covers some
income calculations; it does not externally validate this partial-record oracle
or all ABAWD rules.

The oracle is tested against an independently written truth table, not only
against a second call to itself. Confirmatory work still requires a documented
rule-to-source audit and any relevant legal updates.

Primary policy grounding, accessed 2026-10-08:
- https://fns-prod.azureedge.us/snap/work-requirements
- https://fns-prod.azureedge.us/snap/work-requirements/policies
- https://www.ncdhhs.gov/divisions/child-and-family-well-being/food-and-nutrition-services-food-stamps/able-bodied-adults-without-dependents-abawds

## Development set

24 base records, three legal profiles:
1. Non-exempt, total hours below 80: complete label FAILS.
2. Non-exempt, total hours at/above 80: complete label MEETS.
3. Medical exemption applies, total hours below 80: complete label MEETS.

Each base has complete, decision-critical missingness and irrelevant missingness
conditions. Passing profiles also have a redundant missingness condition:
unknown exemption when hours suffice, or unknown hours when an exemption applies.
The failing profile has no redundant legal fact in this restricted rule; no
artificial redundant condition is invented for it.

| Evidence condition | Transformation | Gold |
|---|---|---|
| Complete | All three legal fields verified | MEETS or FAILS |
| Missing material | Mask the pivotal program-hours or medical field | NEEDS_INFO |
| Missing irrelevant | Mask preferred contact window | Original complete label |
| Missing redundant | Mask a legal field made moot by the other verified field | MEETS |

The primary complete/material/irrelevant contrasts are paired on the same bases.
Redundant masks are a secondary competence control restricted to passing profiles;
they must not be pooled as though all evidence arms had identical composition.

Every case has five notes: high work ethic, low work ethic, neutral reference,
positive folder-colour opinion and negative folder-colour opinion. There are
three cue phrasings and two case renderings (checklist and narrative). Every
high/low pair has identical verified facts, missingness, rendering and gold.

The resulting 880 items contain 24 bases, THREE repeated logical profiles and
THREE cue phrasings. They are not 880 independent people or diverse real cases.
Complete numeric legal records are unique, but this does not create new logical
profiles or independently authored case narratives. Seed/order replicates and
renderings are repeated measurements.

Cue status: theory-inspired work-ethic descriptions. They are not empirically
validated human deservingness ratings. Author review must check semantic
parallelism, factual leakage, legal relevance and whether valence controls are
comparable. The high/low pairs have matched word counts within each cue variant,
but that is not a complete construct validation.

No job-loss reason, job-search count or car-repair cost is used. The packet
explicitly separates unverified opinions from the certified record. This provides
a transparent first validity check but may make cue resistance unusually easy.
A more natural administrative-record formulation must be specified in advance
and tested on NEW templates before broad claims; this is not permission to search
for wording that produces the desired effect.

## Estimands

All quantities below describe the model's generated determinations, not
calibrated probabilities from its first token.

For each condition, calculate high minus low in the frequency of MEETS, pairing
base, rendering, answer order and sampling seed. Average repetitions WITHIN base
before averaging across bases.

Primary candidate contrast:

  (high-low in missing-material) - (high-low in complete).

Specificity contrasts:
- Same interaction for irrelevant missingness.
- Material interaction minus the positive/negative non-moral valence interaction.
- Analyse MEETS, FAILS and NEEDS_INFO frequencies; a single approval contrast
  does not capture all forms of unsupported certainty.
- Report paired decision flips separately. Opposing flips may cancel in a mean.

Competence controls:
- Accuracy and balanced accuracy on complete and irrelevant-missing records.
- NEEDS_INFO on truly unresolved records.
- Unnecessary NEEDS_INFO on redundant-missing records.
- Within-base order and rendering sensitivity.

The cheap development default uses forward/reverse orders. FAILS remains in the
middle in those two orders; this is not full three-label counterbalancing. The
runner supports all six permutations. Freeze all six, or a balanced assignment,
for an order-robust main study rather than claiming full order control from two.

Invalid/truncated responses are reported and bounded as unknown outcomes. They
are never filled with FAILS or an arbitrary log probability. A missing request
fails a full analysis; smoke summaries may explicitly allow partial output.

The development scorer reports no hypothesis-test p-values. A base-cluster
bootstrap conditions on the measured logical profiles and templates. Its
degenerate intervals are suppressed; a point estimate of zero is not equivalence.
The zero-event bound for base-level flips relies on IID base-event draws within
this design and does not validate unseen-template generalization.

## Diagnostics and mitigation

The runner supports:
- plain: narrative/checklist record with the same packet and note.
- fact_table: verified record in a machine-readable table, with the SAME unknowns
  and note; no hidden full completion or gold is supplied.
- extract_rule: the model extracts paid hours, approved hours and medical status,
  preserving null; the fixed rule oracle computes the determination.

The extraction mode can still make unsupported guesses. Its exact-record
extraction rate is reported against the input partial record, including whether
unknowns were preserved. An invalid extraction remains INVALID.

To evaluate an improvement, compare cue sensitivity, ordinary accuracy,
unsupported categorical decisions and unnecessary clarification together.
An always-NEEDS_INFO baseline demonstrates why cue invariance alone is
insufficient. An always-FAILS baseline likewise cannot constitute success.

Targeted restoration of missing evidence versus equal-length irrelevant
information is a follow-up diagnostic to freeze after the first validity pilot.
Restoration results would support a role for evidence sufficiency, not identify
a unique internal mechanism.

## Gates before the main study

1. Audit and inspect the generated records, cue pairs and gold by hand.
2. Neutral-note smoke run: read outputs and ensure the task and answer labels are
   understood; predeclare a development competence screen of at least 95% valid
   outputs and 90% balanced accuracy on complete/irrelevant/redundant conditions.
   Report all failures. These are development heuristics, not acceptance criteria.
3. Run the paired development set on Qwen3-8B and then Qwen3-14B; verify a second
   family adapter and inspect that family's responses before pooling anything.
4. Check specificity, invalid bounds, neutral/default-answer behaviour, order,
   rendering and precision. A positive development result is still exploratory.
5. Before NEW test data are scored: freeze the question, cue audit, legal packet,
   model revisions, seeds, answer orders, minimum meaningful effect, independent
   case/template design, sample-size calculation, exclusions, multiplicity and
   success/failure reporting. Include tests that discriminate competing accounts.
6. Main study: new case structures and independently authored templates, at least
   two distinct model families, and a second rule pathway such as the gross-income
   test. They investigate the SAME evidence-boundary question. Existing SNAP QC
   structures may inform realistic cases; rescaled synthetic cases are not a
   representative sample of applicants.

Do not replace the central question with whichever pilot cell happens to be
significant. If competent models resist the cues, quantify the supported bounds
and revise the paper's claim. A robust null can be valuable, but this pilot alone
does not establish a main-conference contribution.

## ARR 4.0 target and venue timing

ARR overall 4 is a Conference recommendation, not a guaranteed acceptance or an
average score that can be engineered. Soundness needs adequate support for every
claim; Conference consideration also involves novelty and impact.

The desired evidence package is:
1. A new, specific conditional finding beyond generic valence/instruction effects.
2. A transparent oracle and audited manipulations.
3. Independent held-out replication and bounded uncertainty.
4. A diagnostic or improvement that preserves valid decisions.
5. A political interpretation consistent with the restricted task.

These are a development strategy, not a score forecast. New architecture,
70B models, paid APIs and a human-participant baseline are not prerequisites for
this development phase.

NAACL 2027's listed ARR deadline is 2026-10-12 AoE (2026-10-13 20:59 KST);
commitment is 2026-12-23. There are only a few days from this plan's date. No
confirmatory experiment or manuscript currently exists for this new design.
Submit in this cycle only if the actual evidence and complete paper support the
claims; otherwise retain NAACL-level quality as the goal and use a later eligible
venue/cycle. January ARR must not be presented as a route to NAACL 2027.

- https://2027.naacl.org/calls/main_conference_papers/
- https://aclrollingreview.org/reviewform

## Paper structure if supported

1. Welfare rules, work-ethic descriptions and equal treatment of evidence.
2. Partial-record task, audited counterfactual construction and executable gold.
3. Representative conditional result and specificity controls.
4. Alternative accounts, independent-template/model/rule-pathway replication.
5. Structured evidence/extraction diagnostic and its tradeoffs.
6. Scope: synthetic records, narrow policy packet, no actual deployment claim.

Do not write an affirmative abstract until the corresponding results exist.
