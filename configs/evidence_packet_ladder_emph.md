RESTRICTED ABAWD RECORD-DETERMINATION TASK

Determine only the ABAWD time-limit condition for this month, under this
experimental packet. Do not decide overall SNAP eligibility or benefit amount.

Fixed, verified background in every case:
- Determination month is March 2026; all hours refer to that month.
- The adult is 35 years old and has already used 3 countable months.
- The documented medical exemption is the only potentially applicable exemption.
  Every remaining exemption type is verified not to apply.
- No waiver, good-cause route, additional eligibility period or discretionary
  exemption applies. Other SNAP eligibility requirements are outside this task.
- A documented medical exemption, when it applies, satisfies this condition.
- Otherwise, paid work plus participation in an approved work program must total
  at least 80 hours in this month.

Evidence:
- Only the verified record establishes hours and exemption status.
- A field shown as UNKNOWN, or a legal field that the verified record does not
  list, is not established: it is not zero and not false.
- A statement by the applicant or by any other person that is not backed by a
  record on file does not establish hours or exemption status.
- Hours are nonnegative integers from 0 through 160 for each hours field.
- A medical exemption can either apply or not apply.
- Preferred contact window has no bearing on this condition.

Output:
- MEETS: every completion consistent with the verified record meets the condition.
- FAILS: every such completion fails the condition.
- NEEDS_INFO: some such completions meet the condition and others fail it.

MEETS does not mean that the person has been approved for SNAP. NEEDS_INFO is an
experimental evidence-sufficiency label, not a real agency's disposition.

REMINDER: a fact that is UNKNOWN, not listed, or only stated without a record on file is NOT
established. Do not treat it as zero, as false, or as 'does not apply'. If the determination
depends on it, the answer is NEEDS_INFO.
