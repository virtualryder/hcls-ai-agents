# ROI Analysis — Site and Patient Matching Agent (illustrative)

Figures are modeling assumptions for a mid-size sponsor running an active
clinical portfolio; validate against the customer's own baselines during the
assessment. They are not guarantees.

## Where the time goes today

A clinical trial team spends 2–4 weeks per study on manual RWD analysis:
writing cohort specifications, submitting queries to the RWD vendor, waiting
for turnaround, aggregating site counts from spreadsheets, and drafting a
feasibility report — before a single site conversation begins.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| Protocol eligibility criteria review | ~8 hrs | ~30 min | `eligibility_translator` converts to computable CDISC logic |
| RWD cohort query design and execution | ~16 hrs | ~10 min | `run_cohort_query` node via gateway API — same-day |
| Site data aggregation and ranking | ~12 hrs | ~30 min | `cohort_estimator` + `site_ranker` automated |
| Demographic representativeness analysis | ~6 hrs | ~10 min | `fairness_checker` benchmarks against disease-prevalence data |
| Report drafting and review | ~8 hrs | ~30 min (`SITE_SELECTION_LEAD` HITL approval) | `site_ranker` generates ranked report; human approves |
| **Total** | **~50 hrs/study** | **~2 hrs human + ~0.5 hrs agent** | |

Fully-loaded epidemiologist/CTM cost: ~$100/hr blended.

## Illustrative annual value (10-study portfolio)

| Metric | Manual | With Agent | Saving |
|---|---|---|---|
| Cost/study | ~$5,000 | ~$200 | ~$4,800 |
| Annual cost (10 studies) | ~$50,000 | ~$2,000 | ~$48,000 |
| Cycle time (weeks/study) | 3–4 weeks | ~0.5 weeks | 2.5–3.5 weeks |

## Additional value drivers

**Faster site activation**: 3 weeks saved per study at ~$100K/week opportunity
cost = ~$300K/study in avoided delay costs for oncology programs.

**Improved trial diversity**: systematic demographic representativeness flagging
via `fairness_checker` improves compliance with FDA Diversity Action Plan
requirements. Avoiding a single FDA Request for Information saves an estimated
$50K–$100K in remediation and delay costs.

**Consistent methodology**: every cohort query runs against the same computable
CDISC-aligned specification — no analyst-to-analyst variation in eligibility
interpretation.

## Implementation cost (year 1)

| Item | Estimated cost |
|---|---|
| AWS infrastructure (Bedrock, Step Functions, Lambda) | ~$6,000/yr |
| RWD data connector license (platform-dependent) | ~$20,000 |
| Integration and onboarding | ~$20,000 |
| Governance and validation | ~$15,000 |
| **Total year-1 cost** | **~$61,000** |

## Payback period

- Annual saving (direct labor, 10 studies): ~$48,000
- Including site activation delay savings (~$300K/study × even 1 study): payback
  in under 2 months.
- Labor-only payback: approximately 15 months.

## What we measure in a pilot

Baseline vs. agent on: hours-to-feasibility-report, `eligibility_translator`
accuracy vs. manual interpretation, `fairness_checker` flag rate, and cycle
time from protocol receipt to ranked site list. The assessment instruments these
so the business case is the customer's own data, not a generic slide.
