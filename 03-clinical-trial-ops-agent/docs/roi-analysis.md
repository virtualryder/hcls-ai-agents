# ROI Analysis — Clinical Trial Ops Agent (illustrative)

Figures are modeling assumptions for a mid-size sponsor with an active clinical
portfolio; validate against the customer's own baselines during the assessment.
They are not guarantees.

## Where the time goes today

A CRA or CTM spends the majority of monthly monitoring effort on non-analytical
work: pulling status reports from CTMS, manually reviewing eTMF zone gaps against
ICH E6(R2) checklists, drafting EDC queries one-by-one, and assembling a study
health briefing — not on site coaching or risk decisions.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| Study health briefing (CRA + CTM) | ~6 hrs/study/month | ~30 min human review | `study_briefer` auto-assembles; `quality_checker` pre-screens |
| eTMF gap analysis (`analyze_tmf`) | ~3 hrs per review | ~15 min human review | `tmf_analyzer` maps ICH E6(R2) zones automatically |
| EDC query drafting (`draft_queries`) | ~2 hrs per batch | ~20 min approval | `query_drafter` generates; `CLINOPS_LEAD` approves batch |
| Risk scoring / escalation triage (`detect_issues`) | ~1.5 hrs/study/month | ~10 min | `risk_scorer` flags enrollment, query, and visit issues |
| Protocol deviation review | ~2 hrs per incident | flagged automatically | `detect_issues` node detects and surfaces deviations |

**Total human effort per study per month (agent-assisted): ~1.5 hrs — vs. ~18 hrs manual (75% reduction)**

## Illustrative annual value (10-study portfolio)

| Driver | Estimate |
|---|---|
| CRA / CTM hours saved (10 studies × 16.5 hrs × 12) | ~1,980 hrs/yr |
| At blended CRA rate ($85/hr) | ~$168,300/yr |
| Reduced inspection-finding remediation (avg 2 findings/yr @ $50K each) | ~$100,000/yr |
| Faster query closure (days-to-resolution: 12 → 5 days) | ~$40,000/yr (reduced database-lock delay) |
| **Total estimated annual value** | **~$308,000/yr** |

## Risk mitigation value

- ICH E6(R2) TMF inspection readiness: automated gap detection (`tmf_analyzer`)
  before inspection window removes surprise findings estimated at $200K–$2M per
  critical observation.
- GCP deviation tracking: `detect_issues` node surfaces unreported deviations
  in real time; each missed report carries regulatory sanction risk.
- Query rate monitoring: early site coaching from `risk_scorer` prevents data
  lock delays of 4–8 weeks.

## Implementation cost

| Item | Estimated cost |
|---|---|
| AWS deployment (Bedrock + Step Functions + DynamoDB) | $800/month |
| Platform engineering (one-time) | $40,000 |
| CTMS/eTMF/EDC connector validation | $20,000 |
| GxP system validation (IQ/OQ/PQ) | $25,000 |
| **Total year-1 cost** | **~$95,600** |

**Year-1 net value: ~$212,000 | Payback: ~4 months**

## Qualitative benefits

- **Inspection readiness**: automated TMF completeness tracking (`tmf_analyzer`)
  against ICH E6(R2) zones continuously, not just pre-inspection.
- **HITL gate**: every EDC query (`edc.create_query`) requires `CLINOPS_LEAD`
  approval — no autonomous site writes.
- **Audit trail**: 21 CFR Part 11 / GCP-compliant audit entry per node, with
  reviewer identity bound in the approval token.
- **Scalability**: a single agent instance monitors unlimited studies with no
  incremental headcount.

## What we measure in a pilot

Baseline vs. agent on: hours-to-briefing, TMF gap detection rate, EDC query
batch approval time, and days-from-event-to-query-closure. The assessment
instruments these so the business case is the customer's own data, not a generic slide.
