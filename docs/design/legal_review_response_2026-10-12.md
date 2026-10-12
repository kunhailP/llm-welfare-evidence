# Legal review response (received 2026-10-12 from the PI's legal reviewer; answers docs/design/legal_review_brief.md)

Status: recorded verbatim below (Korean, as received) with the design implications drawn by the assistant and to be
confirmed by the PI. The reviewer states it is a general opinion on federal SNAP rules (7 CFR Part 273, Food and
Nutrition Act of 2008, P.L. 119-21), not a state-specific or case-specific legal representation.

## Implications for Design D (assistant's reading of the answers)
| question | answer in short | design consequence |
| --- | --- | --- |
| Q1 unverified = unestablished, not zero | Upheld for hours (273.2(f)(2)); a fact state UNKNOWN must be kept separate from "allowance at this stage" (273.2(f)(3)(ii) lets an *unverified deduction* be excluded, which is not a finding that it is zero) | Gold stays. The paper must say the task is the requirement-status determination, not the benefit computation, so the deduction rule does not apply |
| Q2 statement without record | Neither ignore the statement nor accept it; **NEEDS_INFO with the required verification and alternative verification routes named** (273.2(f)(4)) | This is exactly the `request` protocol (REQUEST named fields); report it as the legally recommended behaviour, not just a mitigation |
| Q3 undocumented medical exemption | "No document, so no exemption" is overbroad: the ABAWD unfit-for-work exception has several verification routes (273.24(c): disability benefits, obvious unfitness, a professional's statement); the ABAWD exception and the medical *deduction* must be kept apart | E2 medical gold NEEDS_INFO **upheld**; GPT-5's reading is the overbroad one. Add the 273.24(c) routes to the paper's description of the error |
| Q4 gross test with one component unverified | Must not pass the household on the verified components alone (273.2(f)(1)(i)); NEEDS_INFO; but if the verified income alone exceeds the limit, failing on that independent ground is possible | Material gold NEEDS_INFO and redundant gold FAILS both **upheld** |
| Q5 E2 wording | E2 is a provisional NEEDS_INFO state; non-submission is not refusal to cooperate (273.2(d)(1)); the final disposition depends on the verification request, deadlines and fault (273.2(h)) | No relabel. The packet already says NEEDS_INFO is not an agency disposition; keep that sentence in the paper |
| Q6 S2 appointments / late forms | Procedural, not substantive: they cannot make hours zero or income over the limit; they can affect the *application's* disposition after the agency's own steps (notice, rescheduling, at least 10 days to provide verification, 273.2(h)(1)) | S2 stays immaterial to the *condition* the task asks about; the paper states that scope explicitly and does not generalise to the final disposition |
| Q7 S0/S1 opinions | Not a basis for any legal finding; must not be used to infer refusal to cooperate | As assumed |
| Q8 fixed ABAWD case | Admissible as an individual hypothetical in which every other exception is verified not to apply; not a general rule: the 80 hours can also be met by unpaid work, volunteering, workfare and combinations, and other exceptions exist | The packet already restricts to the hypothetical; the paper's Limitations must list the omitted routes. (The brief's "March 2026" is the determination month, not an FNS interpretation; clarified) |
| Q9 FY2026 limits | Correct for a March 2026 determination (FY2026: 1 person $1,696, 6 persons $4,675); FY2027 figures apply from 2026-10-01 ($1,729 / $4,806); elderly-disabled rules and state BBCE are outside the packet | No change; the packet fixes March 2026. Note the FY boundary in the paper |
| Recommended structure | Separate (i) claims and evidence, (ii) fact verification and verification duty, (iii) requirement status TRUE/FALSE/NEEDS_INFO, (iv) the final disposition (approve / deny / continue / other statutory handling) | Our labels are (iii). The paper's framing: NEEDS_INFO is not the opposite of failing; it is the state that calls for a verification step, and "unestablished resolved as zero" skips that step |

Overall: the reviewer finds the proposed design direction legally sound, warns against the opposite simplification
(treating every unverified fact as a hold) and asks that each item carry its verification duty, alternative routes,
agency duties and deadlines. The main study's packet should state, per field, which verification routes exist.

## Verbatim response
(The reviewer's full Korean text, as pasted by the PI on 2026-10-12, follows.)

# 미국 SNAP 복지자격 판정 시스템에 관한 법률검토 답변서

검토 기준일: 2026년 10월 12일. 검토 대상: SNAP 자격판정 모델의 UNKNOWN, FALSE, NEEDS_INFO 처리 및 연방규정 준수 여부. 적용 법령: 7 CFR Part 273, Food and Nutrition Act of 2008 및 2025년 개정법(Public Law 119-21)

## I. 종합 법률의견

SNAP 자격판정 과정에서 증거가 부족하다는 사실과 법적 자격요건을 충족하지 못했다는 사실은 구별되어야 합니다. 그러나 이 구별은 미확인 항목을 언제나 심사 보류로 처리하라는 의미는 아닙니다. 연방규정은 확인이 필요한 사항의 종류, 검증의 의무성, 신청인의 협조 여부, 증거 확보를 위한 행정기관의 의무 및 법정 처리기한에 따라 서로 다른 법률효과를 정하고 있습니다. 따라서 모델이 UNKNOWN을 일률적으로 FALSE로 전환하는 것은 법적 오류를 초래할 수 있으며, 반대로 모든 UNKNOWN을 일률적으로 NEEDS_INFO로 처리하는 것 역시 적법한 판정체계라고 보기 어렵습니다.

| 법률적 상태 | 적절한 시스템 처리 |
| --- | --- |
| 자격요건 충족 사실이 확인됨 | TRUE |
| 자격요건 불충족 사실이 확인됨 | FALSE |
| 필수 검증사항이 미확인됨 | NEEDS_INFO |
| 증거 불충분하지만 대체 검증이 허용됨 | 대체 검증 후 판단 |
| 신청인이 명백하게 협조를 거부함 | 법정 요건 확인 후 거절 가능 |
| 신청인이 증거를 제출하지 못함 | 절차 이행 및 지연 귀책 판단 |
| 심사기한이 경과함 | 7 CFR 273.2(h)에 따른 별도 처리 |

특히 7 CFR 273.2(d)는 단순한 자료 미제출과 명백한 협조 거부를 구별합니다. 또한 273.2(f)는 검증절차를, 273.2(h)는 심사 지연의 원인별 처리 방식을 별도로 규율합니다.

## II. 개별 질의에 대한 답변

### Q1. 미검증은 미확정이지 0이 아니라는 해석이 올바른가?
답변: 원칙적으로 타당합니다. 다만 법률상 모든 미검증 사실을 동일하게 취급할 수는 없습니다. 7 CFR 273.2(f)(2)는 자격 또는 급여액에 영향을 미치는 의심스러운 정보를 검증하도록 규정하고 있습니다. 따라서 자료가 없다는 사정만으로 해당 사실이 존재하지 않는다고 단정할 수 없습니다.
(a) ABAWD 근로·프로그램 참여시간: 신청인의 근로시간이 확인되지 않았다는 사실은 실제 근로시간이 0시간이라는 사실과 다릅니다. 근로시간을 입증하지 못하면 법정 절차에 따라 자격인정에 불이익이 발생할 수 있지만, 그 법률효과는 근로시간이 실제로 0시간이라는 사실인정과 구별되어야 합니다. 따라서 근로시간을 단순히 0으로 대체하는 방식은 권고하지 않습니다.
(b) 의료비 공제: 의료비가 확인되지 않은 경우에도 의료비가 실제로 0달러라는 결론이 되는 것은 아닙니다. 다만 7 CFR 273.2(f)(3)(ii)에 따라 미검증 공제를 제외하고 자격 및 급여액을 산정하는 것이 허용되는 경우가 있습니다. 이는 확인되지 않은 의료비를 사실상 0으로 확정하는 것이 아니라, 해당 심사 시점에 공제를 인정하지 않는 법률적 처리입니다. 그러므로 시스템에서는 사실 상태(UNKNOWN)와 현 단계 공제 인정액(0, 단 법령상 요건 충족 시)을 분리하는 것이 적절합니다.

### Q2. 신청인이 면제나 시간을 진술했으나 기록이 없는 경우 어떻게 처리해야 하는가?
답변: 신청인의 진술을 배제해서도 안 되지만, 진술만으로 모든 검증이 완료되었다고 보아서도 안 됩니다. 7 CFR 273.2(f)(4)는 서류에 의한 검증을 주요 방법으로 정하면서도 허용 가능한 검증방법을 하나의 문서형식으로 제한하지 않습니다. 또한 담당기관은 필요한 경우 제3자 확인 등 대체적인 검증수단을 활용할 수 있습니다. 따라서 신청인이 월 80시간 근로했다고 진술하였으나 출석기록을 제출하지 않았다는 사정만으로 근로시간을 0으로 처리하는 것은 부적절합니다. 다만 근로시간의 법정 검증이 요구되는 상황에서는 진술만으로 요건 충족을 확정할 수도 없습니다. 권고 처리: NEEDS_INFO를 부여하되, 필요한 검증자료와 대체 검증방법을 명시해야 합니다. 이때 시스템은 신청인의 주장, 제출된 증거, 검증 의무의 종류 및 검증 완료 여부를 각각 구별하여 저장해야 합니다.

### Q3. 의료비 면제가 문서화되지 않았으면 적용되지 않는다는 판정이 신청 시점에는 가능한가?
답변: 일정한 조건에서는 가능합니다. 그러나 모든 미검증 의료 관련 주장을 동일하게 배제해서는 안 됩니다. 의료 관련 사항은 (1) 의료비 지출에 대한 소득공제와 (2) ABAWD의 신체적·정신적 근로불능 예외로 구분해야 하며, 이 둘은 법적 요건과 검증방법이 다릅니다. 의료비 공제의 경우, 허용되는 절차를 거친 후에도 해당 비용이 확인되지 않았다면 공제를 제외한 급여 산정이 가능할 수 있습니다. 반면 ABAWD 근로불능 예외는 신청인의 상태가 명백한지, 어떤 기관이나 전문가의 확인이 필요한지, 허용되는 검증수단이 무엇인지를 별도로 판단해야 합니다. 따라서 단순히 의료 문서가 존재하지 않는다는 이유만으로 모든 의료 관련 예외를 FALSE로 처리하는 규칙은 지나치게 광범위합니다. 권고: 의료비 공제의 미인정과 ABAWD 예외사유의 미확인을 별도 필드로 관리하십시오.

### Q4. 총소득 테스트에서 일부 소득 구성요소가 미검증인 경우, 검증된 소득만 합산하여 통과시켜도 되는가?
답변: 원칙적으로 허용되지 않습니다. 7 CFR 273.2(f)(1)(i)는 최초 신청 가구의 비면제 총소득에 대한 검증을 요구합니다. 따라서 근로소득 1,000달러는 확인되었으나 비근로소득의 존재 또는 금액이 미확정인 경우, 확인된 1,000달러만으로 최종적인 총소득 적격 판정을 내려서는 안 됩니다. 그러나 예외적으로 소득을 제공하는 제3자의 비협조 등으로 모든 검증시도가 실패하고 다른 검증수단도 이용할 수 없는 경우, 담당자는 최선의 가용정보를 활용하여 인정 소득을 결정할 수 있습니다. 이 경우에도 미확인 소득을 0달러로 취급한다는 일반원칙이 성립하는 것은 아닙니다. 권고: verified_income = 1000, unverified_income = UNKNOWN, gross_income_test = NEEDS_INFO. 다만 이미 확인된 소득만으로도 해당 가구에 적용되는 소득 상한을 초과하고, 다른 법정 예외가 없다는 점이 확인된다면 그 독립적인 사유에 따른 불합격 판단은 가능할 수 있습니다.

### Q5. E2에서 검증 진행 중이라고 진술한 경우의 적절한 결론은?
답변: 제시된 E2 사실관계에서는 검증절차가 진행 중이라는 사정만으로 신청을 거절하거나 검증 실패로 확정하는 것은 부적절합니다. 신청인은 근로불능 예외사유를 주장하고 있으나 관련 검증이 완료되었는지는 확인되지 않았습니다. 그 주장을 곧바로 승인할 수는 없지만, 단순한 서류 미제출이 명백한 협조 거부를 의미하지도 않습니다. 7 CFR 273.2(d)(1)에 따른 협조 거부는 신청인이 협조할 능력이 있음에도 필요한 행위를 명백하게 거부하는 경우와 구별되어야 합니다. 아울러 7 CFR 273.24(c)의 근로불능 예외는 장애급여 수급, 명백한 근로불능 상태 또는 인정되는 전문가의 진술 등 여러 검증경로를 규정하고 있습니다. 법률적 결론: E2는 해당 사실관계에서 NEEDS_INFO가 타당한 잠정 상태입니다. 다만 최종 법률효과는 검증요청 여부, 처리기한 및 지연 귀책에 따라 달라질 수 있습니다.

## III. 심사절차의 적법성에 관한 답변

### Q6. 접수 면담 불참이나 서류 지연이 ABAWD 시간제한 또는 총소득 테스트에 영향을 줄 수 있는가?
답변: 면담 불참 또는 서류 지연은 원칙적으로 절차적 사유입니다. 이를 곧바로 실체적 자격요건의 불충족으로 간주해서는 안 됩니다. 신청인이 면담에 두 차례 불참하였다 하더라도 그 사실만으로 근로시간이 0시간이 되거나 가구 총소득이 기준치를 초과한 것으로 인정되는 것은 아닙니다. 다만 불참이 법령에서 정한 심사 지연 또는 거부 사유에 해당하는 경우에는 신청서 처리에 불이익이 발생할 수 있습니다. 7 CFR 273.2(h)(1)는 신청인에게 지연 책임을 귀속시키기 전에 행정기관이 적절한 조치(통지 및 재예약, 검증자료 제출에 적어도 10일의 기회 부여 등)를 취했는지 판단하도록 규정합니다. 따라서 S2의 면담 불참과 서류 지연을 이유로 ABAWD 및 총소득 항목 자체를 FALSE로 바꾸는 것은 권고하지 않습니다. 다만 S2의 절차적 상태가 신청의 최종 거절이나 계속 보류에 영향을 미칠 수 있다는 점은 별도로 반영해야 합니다.

### Q7. S0/S1의 문장 표현은 법적으로 유의미한가?
답변: 표현 자체보다 그 표현에 대응하는 실제 절차가 중요합니다. 연방규정은 필요한 검증자료의 통지, 적정한 제출기회, 행정기관의 검증 지원, 지연 책임의 귀속, 통지 내용 요건을 실질적으로 구별합니다. 모델이 특정 문구를 근거로 신청인의 거부 의사를 추정하도록 하는 것은 위험합니다. "제출하지 않았다"는 사실과 "제출을 명백하게 거부했다"는 판단은 서로 다릅니다. 권고: S0/S1은 모델의 독립적인 법률판정 근거가 아니라, 법정 절차의 이행 여부를 검토하기 위한 보조정보로 사용하십시오.

## IV. 규칙 패킷의 실체법상 정확성

### Q8. ABAWD의 35세, countable months 3개월, 유급근로와 승인 프로그램 80시간, 의료 면제만 고려하는 2026년 사례는 정확한가?
답변: 사실관계 자체가 곧바로 오류인 것은 아니지만, 해당 설명만으로 법적으로 완전한 판정규칙이라고 볼 수 없습니다. 첫째, 35세는 2026년 ABAWD 시간제한 적용 연령대(P.L. 119-21에 따라 원칙적으로 18~64세)에 포함됩니다. 둘째, 36개월 내 3개의 countable months 사용은 중요한 요소이나 그것만으로 새로운 신청의 적격 여부가 확정되지는 않습니다. 셋째, 월 80시간 요건의 충족 방식은 유급근로와 승인 프로그램 참여에 국한되지 않으며 무급근로, 자원봉사, 결합, workfare 등도 검토해야 합니다. 넷째, 의료적 근로불능 외의 법정 예외 및 적용 면제 가능성도 배제해서는 안 됩니다. 따라서 packet이 의료적 근로불능만 다루는 경우에는 그것이 다른 모든 예외가 존재하지 않는다고 확인된 개별 가상사례인지, 모든 사례에 적용하는 일반 판정규칙인지 명확히 해야 합니다. 질문에 인용된 2026년 3월 FNS 해석의 정확한 문서명과 원문은 제시되지 않았으므로 별도 원문 대조가 필요합니다. 결론: 사례의 설정 자체는 가능하나, 일반 법규칙으로 구현하기에는 일부 요건이 누락되어 있습니다.

### Q9. FY2026의 총소득 기준액 $1,696 및 $4,675는 오류인가?
답변: FY2026 기준으로는 정확합니다. 다만 2026년 10월 현재 적용할 수치는 아닙니다. 1인 가구 FY2026 $1,696 / FY2027 $1,729; 6인 가구 FY2026 $4,675 / FY2027 $4,806; 적용 기간 FY2026 2025.10.1.–2026.9.30., FY2027 2026.10.1.–2027.9.30. (연방 기준 130% 빈곤선, 48개 주 및 DC). packet이 2026년 3월 기준의 과거 사례라면 기존 금액이 맞습니다. 2026년 10월 12일 현재 신규 신청을 판정하는 규칙이라면 FY2027 수치를 적용해야 합니다. 또한 고령자·장애인 가구 특칙 및 주별 BBCE 적용 가능성도 검토해야 합니다.

## V. 모델 설계 변경에 관한 최종 법률의견

| 수정사항 | 법률적 판단 |
| --- | --- |
| Q1~Q3에 검증 대기 해석 및 법령 출처 추가 | 권고. 다만 모든 미검증을 일률적으로 보류해서는 안 됨 |
| Q3에서 미제출 의료비 공제를 별도 처리 | 조건부 권고. 공제 미인정과 근로불능 예외 부인을 구별해야 함 |
| Q5의 E2 정답을 FALSE에서 NEEDS_INFO로 변경 | 원칙적 권고. 다만 미검증 사실의 상태와 신청서의 최종 처분을 구별해야 함 |
| Q6에서 유의미한 절차 지연에 대한 설명 및 정답 수정 | 권고. 실제 통지와 제출기한 등 행정기록 확인 필요 |

추가 권고 판정구조: 신청인의 주장 및 제출자료 → 사실관계 검증 및 법정 검증 의무 판단 → 입증 완료(TRUE/FALSE) 또는 입증 미완료(NEEDS_INFO) 또는 법적 예외(특칙 적용) → 신청 전체에 대한 최종 행정처분(승인 / 거절 / 심사 계속 / 법정 절차에 따른 기타 처리). 연방 SNAP 법률상 어떤 요건이 충족되었는지 판단하는 문제와 신청인에게 어떤 행정처분을 내려야 하는지는 반드시 같은 문제가 아니기 때문입니다. 또한 2025년 개정법의 시행과 관련해 연방규정의 문언, FNS 시행지침 및 개별 주의 운영규칙을 함께 확인해야 합니다.

## VI. 최종 결론

> SNAP 판정 시스템은 신청인의 자격요건 불충족, 증거의 미제출, 검증절차의 미완료 및 신청인의 협조 거부를 법적으로 구별해야 한다. 미검증 사실을 자동으로 부정적인 사실로 전환하는 것은 연방규정에서 정한 검증절차와 신청인의 절차적 권리를 침해할 위험이 있다. 다만 검증되지 않은 사실에 대해 무조건 자격인정을 유보해야 한다는 원칙 역시 성립하지 않는다. 법령이 허용하는 대체 검증, 미확인 공제의 제외, 검증 지연의 귀책 및 심사기한에 관한 개별 규정을 적용해야 한다. 따라서 본 시스템의 NEEDS_INFO는 실체법적 불합격의 반대 개념이 아니라, 추가적인 사실확인 또는 절차적 판단이 필요한 상태를 나타내도록 설계해야 한다.

최종 의견: 제시된 수정 방향은 전반적으로 법률적 타당성이 있습니다. 특히 Q5의 재검토와 Q6의 절차·실체 구별은 필요합니다. 다만 모든 미검증을 보류 처리하는 방식으로 단순화하지 말고, 각 항목마다 검증 의무, 검증의 대체 가능성, 행정기관의 조치 의무 및 법정 처리기한을 명시해야 합니다.

본 답변은 미국 연방 SNAP 법규에 관한 일반적인 법률검토 의견으로, 특정 주의 규칙과 개별 신청인의 완전한 행정기록을 검토한 법률대리 의견은 아닙니다. 실제 심사에 활용하려면 해당 주의 SNAP 매뉴얼과 적용 시점의 FNS 지침을 추가로 대조해야 합니다.
