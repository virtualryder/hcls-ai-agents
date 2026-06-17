# ROI Analysis — Quality CAPA Agent (illustrative)

Figures are modeling assumptions for a mid-size pharmaceutical or medical device
manufacturer; validate against the customer's own baselines during the assessment.
They are not guarantees.

## Where the time goes today

A QA specialist or Qualified Person spends the majority of CAPA processing time
on non-analytical work: locating the complaint record via `qms.get_complaint`,
searching for similar historical events manually, reviewing closed CAPA files,
drafting the investigation narrative, and assembling evidence — not reasoning
about root cause or systemic risk.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| Complaint classification and risk triage (`classify_event`) | ~3 hrs | ~20 min | `complaint_classifier` rules-based + LLM; QMS lookup auto-populated |
| Similar-event search and trend review (`search_similar_events`) | ~4 hrs | ~10 min | `similarity_search` over closed-CAPA corpus via `qms.search_similar` |
| Root cause hypothesis generation (`root_cause_analysis`) | ~6 hrs | ~1 hr | `root_cause_analyzer` Ishikawa/5-Why heuristics; QP validates |
| First-draft CAPA plan authoring (`draft_capa`) | ~8 hrs | ~2 hrs | Grounded LLM draft; `QUALIFIED_PERSON` finalizes |
| Quality check before review (`quality_check`) | manual, error-prone | automated, pre-review | `quality_checker` GMP grounding + completeness |

## Illustrative annual value (site handling ~200 complaints and deviations/year)

| Driver | Estimate |
|---|---|
| QA specialist hours saved (~16 hrs × 200 events) | ~3,200 hrs/yr |
| Fully-loaded value (@ $85/hr blended QA rate) | ~$272K/yr |
| Reduction in repeat events (better root cause + CAPA plans) | strategic upside |
| Faster QMS closure cycle time | improved inspection readiness |
| Fewer audit findings from incomplete or inconsistent CAPAs | reduced regulatory risk |

## Compliance value

- Consistent documentation standards across all CAPA records (21 CFR Part 820,
  ICH Q10) — `quality_checker` enforces pre-review.
- Deterministic grounding check catches invented or untraced numbers before
  `QUALIFIED_PERSON` review.
- Full audit trail per 21 CFR Part 11 for every AI-assisted step, with reviewer
  identity bound in the approval token.
- `QUALIFIED_PERSON` gate at `human_review_gate` cannot be bypassed by application
  code (framework-enforced `interrupt_before`).
- `qms.create_capa_draft` and `qms.close_capa` are both gated by HIGH-RISK
  approval — no autonomous QMS writes occur.

## What we measure in a pilot

Baseline vs. agent on: hours-to-first-CAPA-draft, `QUALIFIED_PERSON` review edit
volume, grounding defects caught pre-review, cycle time from complaint intake to
CAPA closure, and repeat event rate over 6 months. The assessment instruments
these so the business case is the customer's own data, not a generic slide.
