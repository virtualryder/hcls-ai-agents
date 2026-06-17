# Regulatory & Compliance Framework — Regulatory Writing Agent

This agent operates inside a GxP, 21 CFR Part 11, and model-risk control envelope.
It is a **decision-support** system: it drafts and checks; qualified humans decide.

## Context of use (FDA/EMA good-AI principles, Jan 2026)

| Question | Answer for this agent |
|---|---|
| What does the model do? | Assembles evidence and drafts regulated submission text. |
| What does it NOT do? | Decide regulatory strategy; finalize/submit; make medical claims. |
| Who is accountable? | The Regulatory Approver who reviews and signs off. |
| What is the risk if wrong? | A defective draft is caught by grounding/compliance checks + human review before submission. |

Credibility controls are proportional to that risk: grounding verification, prohibited-language checks, prompt version pinning, audit trail, and a framework-enforced human gate.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry (actor, action, data sources, model used). Production sink is append-only (DynamoDB/QLDB).
- **Electronic signature linkage** — at the human gate, a verified reviewer identity (IdP `sub`, roles, signature meaning, timestamp) is bound to the approval.
- **Record integrity** — drafts are versioned; the grounding report is attached to the record.
- **Access control** — RBAC via IdP roles (`REGULATORY_AUTHOR`, `REGULATORY_APPROVER`); only an approver authorizes the RIM write.

## GxP data integrity (ALCOA+)

Attributable, Legible, Contemporaneous, Original, Accurate — plus Complete, Consistent, Enduring, Available. The grounding check enforces *Accurate* (no claim without a source); the audit trail and prompt registry enforce the rest.

## Model risk (SR 11-7 posture)

The prompt is part of the model. Prompts are registered and hash-pinned in `governance/prompt_manifest.json`; CI fails on un-bumped drift. The eval harness (`governance/evals`) is the ongoing performance check over reviewed golden artifacts.

## Promotional / off-label safeguards

The compliance gate blocks absolute and promotional claims ("cure", "guarantee", "completely safe", "best-in-class") and requires balanced benefit-risk language. Off-label content is out of scope by construction (drafting is bounded to the requested, on-label section).

## What is the customer's responsibility

Computer-system validation for the intended use, IdP integration and role mapping, connector validation to RIM/DMS, Bedrock Guardrail configuration, and sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
