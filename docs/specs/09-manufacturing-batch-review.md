# Agent 09 — Manufacturing Batch-Review (spec)

> **Status: roadmap / expansion agent — Documented maturity.** This is the design and the
> cited business case (deck + `gtm/HCLS-DECK-SOURCES.md` §09). Code, tests, and the AWS-native
> rebuild are a follow-up build per `docs/CREATE-A-NEW-AGENT.md`. It extends the suite to the
> **CMC / GxP manufacturing** end of the lifecycle and is the strongest regulated fit after the
> built eight: it follows the same governed review-and-approve pattern with a QA human gate.

## Problem
Batch-record review and out-of-spec (OOS) / deviation investigation are slow, manual, and
senior-labor-heavy. Average review runs ~48 hrs per batch report (up to ~500 hrs for complex
paper-based records); 21 CFR 211.192 (production-record review / discrepancy investigation) is
among the most-cited FDA warning-letter findings; right-first-time for complex biologics often
sits ~80%, and a single biologics batch failure can cost tens of millions. 62% of US drug
shortages trace to manufacturing/quality problems.

## What the agent does (and the bright line)
"Review by exception": the agent reads the electronic batch record + process/QC data, checks
against limits and required steps, flags deviations / OOS / missing e-signatures, and drafts the
disposition (exception report + recommended release/hold). **A QA reviewer makes the final
release/reject decision and signs it** — the agent never releases a batch.

## Governed pipeline
1. **Read EBR + MES/LIMS** — batch record + process/QC data via gateway-scoped connectors.
2. **Check by exception** — limits, OOS, missing steps, e-signature completeness.
3. **Draft disposition** — exception report + recommended release/hold, every flag traced to data.
4. **HUMAN GATE (QA)** — a named QA reviewer approves release / reject (21 CFR Part 11 e-signature).
5. **Append-only audit** — every check + decision logged with lineage.

## AWS architecture (reuses the shared control plane)
- **Systems of record (new connectors):** MES / electronic batch records (e.g. Körber, Tulip,
  Rockwell, AVEVA), LIMS (QC results). Add the connector kind(s) to `infra/cloudformation/connectors.yaml`.
- **Runtime:** event-driven worker (EventBridge) triggered on batch completion; review/exception agent.
- **Model layer:** in-VPC Bedrock + Guardrails; anomaly/limit checks are deterministic where possible.
- **Data tier:** Aurora/DynamoDB state; DynamoDB append-only audit; S3 Object Lock (WORM) for the
  signed disposition; Secrets Manager scoped tokens.
- **Governance:** grounding = every flagged exception traces to a record value; HITL = QA release
  gate (Step Functions `waitForTaskToken` / AgentCore approval); 21 CFR Part 11 + GMP (21 CFR 211)
  audit posture; CSV/CSA is the production gate.

## Cited business case (see deck + sources §09)
Headline 62% of shortages = manufacturing/quality (FDA). Cost of doing nothing: ~2.1% of sales in
routine quality failure (McKinsey LS proxy) and a modeled ~$420K/yr investigation labor at 200
batches/85% RFT, before scrapped-batch ($1–2M+) cost. Outcome anchors: review-by-exception ~80%
release-time cut (trade), >50% deviation reduction at a benchmarked site (McKinsey).

## To build (flagship depth)
LangGraph workflow with the QA gate · MES + LIMS gateway tools + a limit/OOS checker + a
demo-fallback drafter · 3 deterministic fixtures (1 clean batch, 1 minor deviation, 1 OOS) ·
flagship test suite incl. the release-gate test · Streamlit dashboard · 4-doc set · AWS-native
rebuild under `aws-native-reference/09-manufacturing-batch-review/`. Cited deck already built.
