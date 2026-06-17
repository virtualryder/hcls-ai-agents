# ROI Analysis — Medical Affairs MSL Agent (illustrative)

Figures are modeling assumptions for a mid-size pharma company; validate against
the customer's own baselines during the assessment. They are not guarantees.

## Where the time goes today

A Medical Science Liaison spends 30–50% of pre-call preparation time manually
gathering HCP profile data from CRM via `crm.get_hcp`, locating approved
materials in the DMS via `dms.get_document`, cross-checking content against the
prescribing information, and writing the brief — before any scientific exchange
planning begins.

## Modeled impact

| Workflow | Before | After | Basis |
|---|---|---|---|
| HCP profile pull and summarize (`pull_hcp_and_content`) | ~45 min/meeting | ~2 min | `hcp_profiler` + `crm.get_hcp` gateway; auto-enriched |
| Locate and retrieve approved documents | ~30 min | ~1 min | `content_retriever` + `dms.get_document` auto-retrieval |
| Profile enrichment and next best action (`enrich_and_validate`) | manual, inconsistent | automated | `next_best_action` surfaces interaction history and NBA |
| Draft pre-call brief (`draft_brief`) | ~60 min | ~5 min | `brief_drafter` LLM draft from approved content only |
| Compliance pre-check (`compliance_check`) | manual, inconsistent | automated, pre-review | `compliance_checker` off-label, promotional, grounding |
| `MEDICAL_AFFAIRS_APPROVER` review time | 30 min (from scratch) | 10 min (reviewing AI draft) | Pre-screened draft |
| MLR submission prep (`finalize`) | ~20 min | ~5 min (gateway-automated) | Scoped token + `mlr.submit_for_review` |

## Illustrative annual value (field force of 50 MSLs × 200 meetings/year)

| Driver | Estimate |
|---|---|
| Prep time saved (~2 hrs × 10,000 meetings) | ~20,000 hrs/yr |
| Fully-loaded value (@ $80/hr blended MSL/MA rate) | ~$1.6M/yr |
| Compliance incidents avoided | reduced MLR rejection rate, lower regulatory risk |
| Faster CRM logging (NBA prompts auto-generated) | improved data quality for targeting |

## MSL-specific value drivers

- **Scientific exchange quality**: the `brief_drafter` pre-call brief with full
  data context from `hcp_profiler` lets the MSL focus on the scientific
  conversation rather than note-gathering during the call.
- **Compliance confidence**: the deterministic `compliance_checker` off-label gate
  provides a defensible audit trail for every HCP interaction — critical in FDA
  and EMA enforcement environments.
- **KOL engagement**: tier classification and interaction history surfaced
  automatically by `enrich_and_validate` enables more strategic field-force
  planning.

## What we measure in a pilot

Baseline vs. agent on: prep time per meeting, `MEDICAL_AFFAIRS_APPROVER` review
time, MLR rejection rate, `compliance_checker` finding rate, and CRM data
completeness post-call. The assessment instruments these so the business case
is the customer's own data, not a generic slide.
