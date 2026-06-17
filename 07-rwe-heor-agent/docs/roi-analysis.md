# ROI Analysis — RWE/HEOR Evidence Agent (illustrative)

Figures are modeling assumptions for a mid-size pharma sponsor; validate against
the customer's own baselines during the assessment. They are not guarantees.

## Where the time goes today

A health economics and outcomes research team spends the majority of study cycle
time on non-analytic work: writing cohort specifications (`define_cohort`),
waiting for RWD platform query turnaround, manually extracting statistics from
vendor reports, and drafting narrative sections from spreadsheets — not on
epidemiological reasoning or interpretation.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| Cohort definition to first query (`define_cohort`) | ~2 weeks | ~2 hours | `cohort_definer` generates computable ICD-10 spec automatically |
| Query turnaround (`run_cohort_query`) | 3–5 business days (internal RWD team) | same-day | `rwd.run_cohort_query` direct gateway API |
| Data quality assessment (`assess_data_quality`) | manual, ad-hoc | automated, pre-synthesis | `data_quality_assessor` completeness, balance, confounding checks |
| Evidence synthesis first draft (`synthesize_evidence`) | ~8 hrs | ~30 min | `evidence_synthesizer` grounded narrative from pre-computed stats |
| Grounding and traceability check (`grounding_check`) | manual, error-prone | automated, pre-review | `rwe_checker` — numbers traceable, no causal claims |
| `EPIDEMIOLOGIST` review time | ~4 hrs/study (verification from scratch) | ~1 hr/study (sign-off on pre-screened synthesis) | Pre-screened synthesis |

## Illustrative annual value (sponsor running ~40 RWE studies/year)

| Driver | Estimate |
|---|---|
| Analyst hours saved (cohort spec + synthesis, ~18 hrs × 40) | ~720 hrs/yr |
| Fully-loaded value (@ $150/hr blended HEOR rate) | ~$108K/yr |
| Faster query turnaround (cycle-time reduction per study) | 2–3 weeks per study |
| Reduced revision cycles (`rwe_checker` catches errors pre-review) | 30–50% fewer revisions |
| Earlier payer submissions / formulary decisions | strategic upside |

## HEOR-specific value drivers

- **Payer dossier cycle time**: real-world evidence is a critical dossier
  component; faster synthesis via `evidence_synthesizer` accelerates AMCP/NICE/HTA
  submissions.
- **Label expansion support**: RWE packages built faster reduce time-to-evidence
  for supplemental applications.
- **Formulary negotiations**: timely cost-effectiveness analyses support
  contracting cycles.
- **Statistical integrity**: the compute-first, LLM-second architecture
  (`assess_data_quality` before `synthesize_evidence`) ensures the LLM never
  fabricates statistics — a critical differentiator for regulatory submissions.

## What we measure in a pilot

Baseline vs. agent on: hours-to-first-synthesis, `EPIDEMIOLOGIST` edit volume,
grounding defects caught by `rwe_checker` pre-review, and cycle time from
research question to approved synthesis. The assessment instruments these so the
business case is the customer's own data, not a generic slide.
