# Agent 09 — ROI Analysis

> Figures trace to `gtm/HCLS-DECK-SOURCES.md` §09 and are modeled at the customer's baseline —
> not guaranteed. See `gtm/roi-calculator/` once 09 is added to the calculator.

## The pain (cited)
- **62%** of US drug shortages trace to manufacturing/quality problems — the #1 root cause (FDA).
- Average review **~48 hrs per batch report** today (up to ~500 hrs for complex paper-based) `[sector-press]`.
- **~$14K** average cost per deviation investigation, mostly senior labor `[sector-press]`.
- **21 CFR 211.192** record-review is among the most-cited FDA warning-letter findings `[gov]`.

## Modeled value (show the arithmetic)
At **200 commercial batches/yr** and **85% right-first-time**, ~30 batches/yr generate exceptions.
- Investigation labor: 30 × ~$14K ≈ **~$420K/yr** before any scrapped-batch ($1–2M+ each) or
  delayed-release carrying cost.
- Review-by-exception is documented to cut batch-release time **~80%** (compressing a ~150-page
  record to a ~3-page exception report) `[sector-press — illustrative]`.
- A benchmarked biopharma site cut product deviations **>50%** and waste **~75%** `[industry-research — McKinsey]`.

## What's defensible vs. flagged
Lead with the FDA 62% and the McKinsey >50% deviation reduction. The 48-hr review, $14K investigation,
and ~80% RBE figures are sector/vendor-adjacent estimates — present as benchmarks, not guarantees.
No independent AI batch-review ROI benchmark is established; the value case is the modeled
investigation labor + avoided scrapped-batch/shortage risk + review-cycle compression.

## Cost to run
Bedrock inference is modest (the LLM drafts only the human-readable report; the pass/fail scan is
deterministic). Model the Bedrock run-rate + per-customer infra via `offerings/TCO-MODEL.md`.
