# ROI Analysis — Pharmacovigilance ICSR Intake Agent (illustrative)

Figures are modeling assumptions for a mid-size MAH processing ~3,000 ICSRs/year;
validate against the customer's own baselines during the assessment. They are not
guarantees.

## Where the time goes today

A PV processor spends the majority of case-intake time on non-cognitive work:
reading and parsing source records, manually transcribing fields into the safety
database, looking up MedDRA and WHODrug codes, checking for duplicates, and
writing the CIOMS narrative — not assessing signal or seriousness.

## Modeled impact

| Workflow step | Before | After | Basis |
|---|---|---|---|
| Source record parsing to E2B fields | ~45 min/case | ~5 min/case | Auto-extraction |
| MedDRA PT + WHODrug coding | ~15 min/case | ~2 min/case | Gateway-backed coder |
| Duplicate search | ~10 min/case | automated | safety.search_duplicates |
| Seriousness + clock determination | ~10 min/case | automated | ICH E2A heuristic |
| CIOMS narrative drafting | ~30 min/case | ~5 min/case | Grounded LLM draft |
| Quality / element check | manual, inconsistent | automated, per-case | quality_checker |
| **Total per case** | **~110 min** | **~15 min** | **86% reduction** |

## Illustrative annual value (MAH processing 3,000 ICSRs/year)

| Driver | Estimate |
|---|---|
| PV processor hours saved (~95 min × 3,000) | ~4,750 hrs/yr |
| Fully-loaded value (@ $85/hr blended) | ~$404K/yr |
| Expedited reporting compliance (7-/15-day clocks) | reduced regulatory risk |
| Fewer duplicate submissions | reduced duplicates penalty risk |
| Faster signal detection (structured coded data) | strategic safety upside |

## Compliance risk value

Missed 15-day expedited reporting deadlines: FDA warning letters, EMA non-compliance
findings, and marketing-authorization consequences. The seriousness assessor and
reporting clock are computed automatically for every case — the risk of a missed
clock is reduced from a processor oversight to a system-design question.

## What we measure in a pilot

Baseline vs. agent on: minutes-per-case end-to-end, MedDRA coding accuracy (vs.
licensed coder benchmark), duplicate detection rate, seriousness classification
accuracy (vs. PV Medical Reviewer adjudication), and narrative element completeness.
The assessment instruments these so the business case is the customer's own data.
