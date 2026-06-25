# Agent 09 — Regulatory & Compliance Design

**Context of use.** The agent reads an electronic batch record (EBR/MES) and QC results (LIMS),
scans **by exception** for deviations / OOS / missing steps / incomplete e-signatures, and drafts a
disposition (exception report + release/hold recommendation). It **does not release or reject a
batch** — a Qualified Person / QA reviewer signs the disposition at the gateway.

## Regulatory mapping

| Requirement | How the agent meets it |
|---|---|
| **21 CFR 211.192** (production-record review; investigation of discrepancies) | The exception scan is the documented review; every flagged discrepancy is captured with its source and routed to QA. This clause is among the most-cited FDA warning-letter findings. |
| **21 CFR Part 11** (electronic records / signatures) | Append-only audit (DynamoDB + S3 Object Lock WORM) with actor, timestamp, sources, model + prompt version; the QA disposition is recorded only with a verified reviewer identity bound at the gateway (e-signature linkage). |
| **cGMP 21 CFR 211** (batch production & control records) | The agent never alters the batch record; it produces a separate, traceable exception report and recommendation. |
| **ALCOA+ (data integrity)** | Every figure/entity in the exception report traces to the batch record or LIMS result (grounding check fails fast on an ungrounded claim). Prompts are hash-pinned in the governance registry. |
| **EU GMP Annex 11 / data integrity** | Same controls apply for EU-regulated sites; per-customer VPC isolation and CSV are the production gate. |

## The bright line (what the agent never decides)
Batch **release or reject**. The agent recommends; a named QA reviewer / Qualified Person decides
and signs. The HITL gate is framework-enforced (`interrupt_before=["human_review_gate"]`), not a
procedural SOP — application code cannot bypass it.

## Validation posture (CSV/CSA)
This is a **Documented/Demonstrated** reference accelerator. Production use requires computer-system
validation (IQ/OQ/PQ) under the customer's quality system, a traceability matrix from this design to
executed tests, and periodic review. The deterministic exception scanner is intentionally simple and
testable so its OQ is tractable; the LLM drafts only the human-readable narrative, never the
pass/fail decision.

## Records & retention
Batch-review records inherit the product's batch-record retention (≥1 year past expiry; often longer).
`DATABASE_URL` enables PostgresSaver for durable, resumable review state across restarts.
