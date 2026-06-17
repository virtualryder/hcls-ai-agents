# Regulatory & Compliance Framework — Quality & CAPA Agent

This agent operates inside a FDA QMSR, ISO 13485, 21 CFR Part 11, and MDR vigilance control envelope.
It is a **decision-support** system: it classifies, drafts, and detects; Qualified Persons decide and authorize.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Queries historical QMS events, classifies severity, generates root cause hypotheses, and drafts a CAPA plan. |
| What does it NOT do? | Create QMS records autonomously; determine regulatory reporting obligation; adjudicate root cause. |
| Who is accountable? | The Qualified Person who reviews and approves before any QMS record is created. |
| What is the risk if wrong? | A defective CAPA plan is caught by structural/grounding checks and QP review before the QMS record is opened. |

## FDA QMSR (21 CFR 820, effective February 2026)

The Quality Management System Regulation, effective February 2026, aligns FDA requirements with ISO 13485:2016. This agent supports QMSR compliance by:

- **Systematic CAPA procedure** — the workflow enforces containment → root cause investigation → correction → prevention → effectiveness monitoring as the required sequence.
- **Root cause analysis** — hypothesis generation uses structured methodologies (five-why, fishbone categories) applied to the specific event type.
- **Effectiveness check** — every CAPA plan includes a time-bound effectiveness monitoring section with a defined recurrence metric, as required by QMSR § 820.100.
- **Trend analysis** — historical QMS query surfaces the number of similar events, supporting the trend-reporting requirement.

## ISO 13485:2016 alignment

ISO 13485 clause 8.5.2 (Corrective Action) and 8.5.3 (Preventive Action) require documented procedures with defined roles and effectiveness verification. The agent's quality gate enforces the presence of all ISO 13485-required CAPA elements before QP review.

## EU MDR Vigilance (Articles 87–90) and 21 CFR 803 MDR

- The CAPA plan includes a regulatory assessment section prompting the QP to evaluate whether the event meets serious incident (EU MDR) or reportable event (21 CFR 803) thresholds.
- The agent does NOT make the reporting determination; it surfaces the assessment item and routes to the QP, who is responsible for the final decision and any regulatory notification.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry. Production sink is append-only (DynamoDB/QLDB).
- **Electronic signature linkage** — at the human gate, a verified QP identity (IdP `sub`, role, timestamp) is bound to the approval before the QMS record is created.
- **Record integrity** — CAPA plans are versioned; the grounding report is attached to the record.
- **Access control** — RBAC via IdP roles (`QA_MANAGER`, `QUALIFIED_PERSON`); only a QP role authorizes the QMS write.

## GxP data integrity (ALCOA+)

The grounding check enforces *Accurate*: every number in the CAPA plan must be traceable to the event data and QMS query state. No root cause hypotheses, lot numbers, or event counts are fabricated by the model. The audit trail enforces the remaining ALCOA+ principles.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`. The speculative-language gate blocks causal conclusions ("definitely caused by") — all root causes are framed as hypotheses pending investigation, as required by GxP data integrity principles.

## Customer responsibilities

Computer-system validation for the intended use, IdP integration and QP role mapping, QMS connector validation, Bedrock Guardrail configuration, and QP sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
