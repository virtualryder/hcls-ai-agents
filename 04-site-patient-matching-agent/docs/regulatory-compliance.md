# Regulatory & Compliance Framework — Site & Patient Matching Agent

This agent operates inside a GCP, HIPAA minimum-necessary, and FDA Diversity Action Plan control envelope.
It is a **decision-support** system: it estimates, ranks, and flags; qualified humans authorize every outreach decision.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Queries de-identified aggregate patient data, ranks sites by feasibility and diversity profile, and drafts a matching report. |
| What does it NOT do? | Access patient-level PHI; initiate site contact autonomously; make enrollment decisions. |
| Who is accountable? | The clinical team lead who reviews and approves the ranking before any outreach. |
| What is the risk if wrong? | An inaccurate feasibility estimate delays enrollment or biases site selection; grounding checks and human review catch errors before action. |

## FDA Diversity Action Plan compliance (2024 final guidance)

FDA expects sponsors to submit a Diversity Action Plan for most trials of drugs and biologics. This agent supports that plan by:

- **Proactive demographic analysis** — the fairness checker evaluates the eligible cohort demographic breakdown against configurable benchmarks at the point of site selection, before activation.
- **Severity-rated flags** — under-represented groups are flagged with HIGH/MODERATE/LOW severity, giving the clinical team a prioritized action list.
- **Audit trail** — all fairness findings are recorded in the append-only audit trail, providing evidence for the DAP submission.

## HIPAA minimum necessary / de-identification (45 CFR 164.514)

- All patient cohort queries return **aggregate counts only** — no patient-level records are transmitted to the agent or stored in its state.
- The gateway enforces aggregate-only query contracts; any response containing patient-level identifiers is rejected.
- The drafted report must include a PHI/de-identification note (enforced by the quality gate's `phi_note` structural check).
- Production deployments should configure RWD platform connectors to apply safe-harbor de-identification or expert-determination de-identification before data reaches the gateway.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry. Production sink is append-only (DynamoDB/QLDB).
- **Authorization linkage** — at the human gate, a verified reviewer identity is bound to the approval before any site outreach workflow is triggered.
- **Record integrity** — reports are versioned; grounding and fairness reports are attached to the record.

## GxP data integrity (ALCOA+)

The grounding check enforces *Accurate*: every number in the feasibility report must be traceable to the cohort query result in state. The audit trail enforces the remaining ALCOA+ principles.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`. The deterministic demo mode (no API key) supports validation evidence generation and CI testing without live data.

## Customer responsibilities

De-identification validation for the chosen RWD platform connector, IdP integration and role mapping, site registry connector validation, Bedrock Guardrail configuration, and clinical-team sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
