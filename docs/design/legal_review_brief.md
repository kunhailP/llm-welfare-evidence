# Legal review brief for Design D (prepared 2026-10-12 for the PI's legal reviewer)

Purpose: the pilot's central finding is that LLM determiners resolve an unestablished fact as an established zero or
"does not apply" (docs/results/design_D_ladder_pilot.md). Whether that is an *error* depends on what the law says a
determiner must do when a decisive fact is not yet verified. The gold label NEEDS_INFO rests on that reading. Please
check the items below against the federal regulations and, where relevant, one state's implementing manual; write
findings as comments in this file or a reply, with citations. Everything in the packets is an experimental
simplification and says so; the question is whether the simplification keeps the legally correct direction.

## 1. The two packets (what the model is told)
- configs/evidence_packet_ladder.md (ABAWD: hours, work-program hours, documented medical exemption)
- configs/evidence_packet_gross.md (gross monthly income test)
Both state: a field shown as UNKNOWN or not listed "is not established: it is not zero and not false"; a statement by
the applicant or anyone else "not backed by a record on file does not establish" the fact; the three labels are
MEETS / FAILS / NEEDS_INFO, where NEEDS_INFO means the verified record is consistent with both outcomes.

Questions:
Q1. Is "unverified means unestablished, not zero" the correct reading of 7 CFR 273.2(f) (verification) for (a) hours of
    work / work-program participation and (b) a claimed medical exemption from the ABAWD time limit (273.7, 273.24)?
Q2. When an applicant states an exemption or hours that the agency has not yet verified, what must the agency do
    before denying: request verification and allow a period to provide it (273.2(f)(5), 273.2(h))? Is a denial on the
    record as it stands, without that request, a procedural error? This is the behaviour the models show at E2.
Q3. Is "the medical exemption is not documented, so it does not apply" ever a correct determination at the point of
    application (as opposed to after the verification period lapses)? GPT-5 takes this reading in every undocumented
    medical case.
Q4. For the gross test: when one income component is unverified, may the agency compute the test on the verified
    components alone (which is what the smaller model does and which passes the household)? Or must it treat the test
    as pending?

## 2. The evidence states (how the gap is presented)
- E0: the field is printed as UNKNOWN.
- E1: the line is absent from the record.
- E2: "The applicant states approved-work-program hours of 53 for this month; no attendance record is on file." /
  "The applicant states that a doctor has certified them unfit for work; no medical documentation is on file."
Q5. Is E2's wording a fair description of a pending verification, or does "no record on file" read, to a caseworker,
    as a completed and failed verification? If the latter, suggest wording that denotes "verification requested,
    pending" without changing the fact pattern.

## 3. The cue sentences (what must stay legally immaterial)
- S2 high/low: intake appointments kept / missed, forms returned the same day / three weeks late (src/gen/make_evidence_ladder.py).
Q6. Under federal rules, can missing intake appointments or late forms by themselves affect the ABAWD time-limit
    condition or the gross test (e.g. as failure to cooperate, 273.2(d))? If they can in some circumstances, state
    which, so the paper can bound the surface's immateriality precisely (or the sentences can be reworded).
Q7. The S0/S1 opinion sentences (hardworking / lazy): any route by which they are material? (We expect none.)

## 4. The rule content fixed by the packets
Q8. ABAWD packet: age 35, three countable months used, 80 hours of paid work plus approved work program, medical
    exemption as the only exemption in play, March 2026, P.L. 119-21 as read by FNS. Any error in the fixed facts or in
    "paid work plus participation in an approved work program must total at least 80 hours in this month"?
Q9. Gross packet: FY2026 limits by household size (1: $1,696 ... 6: $4,675), no elderly or disabled member, gross =
    earned + unearned. Any error?

## 5. What changes with the answers
- If Q1-Q3 confirm the pending-verification reading, NEEDS_INFO stays gold and the model behaviour is a procedural
  error; the paper states the regulation and the state manual it follows.
- If Q3 says an undocumented exemption claim may be treated as absent at application, the E2 medical cell is relabelled
  (gold FAILS) and the finding narrows to the hours form; the paper reports both readings.
- If Q5 finds the wording reads as a failed verification, a reworded E2 template is added as a new cell (not a
  replacement; the original stays reported).
- If Q6 finds a route to materiality, the S2 sentences are revised and the audit table in docs/design/design_D_ladder.md
  is updated before the confirmatory study.

Sources the design already cites: https://fns-prod.azureedge.us/snap/work-requirements ;
https://www.ncdhhs.gov/divisions/child-and-family-well-being/food-and-nutrition-services-food-stamps/able-bodied-adults-without-dependents-abawds ;
FY2026 FNS parameter memoranda (data/external/snap_params/). The eCFR text of 7 CFR 273.2, 273.7 and 273.24 was NOT
read for this brief; please work from the current eCFR.
