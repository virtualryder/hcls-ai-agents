# ROI Analysis — Protocol Design Agent (illustrative)

Figures are modeling assumptions for a mid-size clinical-stage sponsor;
validate against the customer's own baselines during the assessment. They are not
guarantees.

## Where the time goes today

A clinical scientist or medical writer spends the majority of protocol authoring
time on non-creative work: locating relevant regulatory guidance via manual RIM
searches, waiting days-to-weeks for RWD vendor turnaround on feasibility queries,
reviewing historical study designs in CTMS, and assembling evidence before a
single word of the protocol is written.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| Regulatory guidance identification (`search_guidance`) | 2–4 hrs per protocol | ~10 min | `guidance_searcher` + `rim.search_guidance` auto-retrieval and relevance scoring |
| RWD feasibility query and interpretation (`feasibility_estimate`) | 1–2 weeks (vendor turnaround) | ~2 hrs | `rwd.run_cohort_query` direct gateway API — same-day |
| Historical study precedent review | ~8 hrs | ~30 min | `ctms.get_study_status` automated precedent lookup |
| First-draft protocol sections (`draft_protocol_sections`) | ~20 hrs | ~4 hrs | `protocol_drafter` grounded LLM draft; `MEDICAL_REVIEWER` finalizes |
| Quality check before review (`quality_check`) | manual, error-prone | automated, pre-review | `protocol_checker` regulatory completeness + grounding |

## Illustrative annual value (sponsor running ~15 protocols/year)

| Driver | Estimate |
|---|---|
| Clinical scientist hours saved (~28 hrs × 15) | ~420 hrs/yr |
| Fully-loaded value (@ $150/hr blended rate) | ~$63K/yr |
| Reduction in protocol amendments (better upfront feasibility from `feasibility_estimator`) | strategic upside |
| Faster IND/CTA preparation cycle time | earlier study start; earlier data |
| Fewer amendment cycles from avoidable eligibility errors | reduced costs and delays |

## Compliance value

- All regulatory guidance sourced from RIM via `rim.search_guidance` and linked
  to protocol decisions — traceable at every section.
- `rwd.run_cohort_query` returns aggregate, de-identified counts only
  (HIPAA Safe Harbor / k-anonymity) — no PHI enters the protocol draft.
- `protocol_checker` grounding check prevents invented patient counts from
  entering the protocol sections.
- Full ICH E6(R2) audit trail for every AI-assisted drafting step.
- `CLINICAL_SCIENTIST` and `MEDICAL_REVIEWER` gate at `human_review_gate` cannot
  be bypassed by application code (framework-enforced `interrupt_before`).

## What we measure in a pilot

Baseline vs. agent on: hours-to-first-draft, reviewer edit volume, number of
guidance documents missed by manual search vs. `guidance_searcher`, feasibility
query turnaround time, and number of eligibility-related protocol amendments over
12 months. The assessment instruments these so the business case is the customer's
own data, not a generic slide.
