# HCLS AI Agent Suite — ROI Calculator

`HCLS-AI-Suite-ROI-Calculator.xlsx` turns the cited cost-of-doing-nothing anchors in
[`../HCLS-DECK-SOURCES.md`](../HCLS-DECK-SOURCES.md) into a per-agent, **customer-specific**
ROI model an AWS SA or SI lead can fill in live with a prospect.

## How to use

1. Open the **Assumptions** tab and set the blue input cells to the customer's baseline (loaded labor rates, day-of-delay value, per-agent Bedrock + infra run-rate from your TCO model).
2. Open each **agent tab** and set the blue per-agent inputs (volumes, hours, expected reduction %).
3. Read the green **Net modeled annual value** on each tab and the **Summary** tab for the suite roll-up.

Only blue cells are inputs; everything else is a formula. The expected-reduction percentages are planning assumptions the SA sets *with* the customer — they are not vendor promises.

## What's modeled (and the anchor behind it)

| Tab | Driver model | Anchor |
|---|---|---|
| 01 Regulatory Writing | writer hours saved + delay-days avoided × sales/day | Merck ~40–55% draft cut; Tufts $800K/day |
| 02 Pharmacovigilance | case-processing hours × reduction × rate | Schmider 40–70%; ~69 min/case |
| 03 Clinical Trial Ops & TMF | slip-days avoided × (lost sales + Phase III direct/day) | Tufts CSDD 2024 |
| 04 Site & Patient Matching | enrollment days pulled in × sales/day + wasted activations | Tufts 2024; activation benchmarks |
| 05 Quality / CAPA | investigation hours × reduction × rate (+ recall exposure) | FDA inspection data; recall-cost range |
| 06 Protocol Design | avoidable amendments prevented × ($535K + delay days) | Tufts CSDD 2016 + 2024 |
| 07 RWE / HEOR | analyst FTE × loaded cost × prep-time share reclaimed | Anaconda ~45% |
| 08 Medical Affairs / MSL | review hours × reduction × rate | McKinsey 50–70% |

## Regenerate

```bash
pip install openpyxl --break-system-packages
python3 gtm/roi-calculator/generate_roi_calculator.py
```

> **Discipline:** every figure is modeled at the customer's own baseline and is **not guaranteed**. Pair it with the cited decks and the TCO model in `offerings/TCO-MODEL.md`. Land-first agents 01/02/03/08 typically anchor the Phase-1 business case.
