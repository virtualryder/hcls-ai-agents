# Regulatory & Compliance Framework — Clinical Trial Operations Agent

This agent operates inside a GCP, 21 CFR Part 11, and ICH E6(R3) control envelope.
It is a **decision-support** system: it monitors, detects, and drafts; qualified humans decide and authorize.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Pulls study health data and drafts an operational briefing for ClinOps Lead review. |
| What does it NOT do? | Create EDC queries autonomously; adjudicate protocol deviations; modify trial data. |
| Who is accountable? | The ClinOps Lead who reviews and approves before any EDC write. |
| What is the risk if wrong? | A defective briefing is caught by grounding/quality checks and human review before any site action. |

## ICH E6(R3) GCP controls

The agent implements centralized monitoring principles from ICH E6(R3):

- **Continuous data review** — enrollment pace, visit completion, and query rates are calculated per review cycle, not only at monitoring visits.
- **Risk-based issue detection** — configurable thresholds flag HIGH/MEDIUM issues for prioritization rather than treating all gaps equally.
- **TMF completeness** — document completeness percentage is surfaced alongside subject-level data to give a complete inspection-readiness picture.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry (actor, action, data sources accessed, model used). Production sink is append-only (DynamoDB/QLDB).
- **Electronic authorization linkage** — at the human gate, a verified reviewer identity (IdP `sub`, roles, timestamp) is bound to approval before any EDC query is created.
- **Record integrity** — briefings are versioned; the grounding report is attached to the record.
- **Access control** — RBAC via IdP roles (`CLINOPS_LEAD`, `CRA`); only a ClinOps Lead role triggers the finalize write path.

## GxP data integrity (ALCOA+)

Attributable, Legible, Contemporaneous, Original, Accurate — plus Complete, Consistent, Enduring, Available. The grounding check enforces *Accurate* (no number in the briefing without a traceable source in CTMS/eTMF/EDC state); the audit trail enforces the rest.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`; CI fails on un-bumped drift. The eval harness (`governance/evals`) provides ongoing performance checks. Demo mode is fully deterministic and requires no API key, supporting validation evidence generation.

## PHI handling

Subject-level data accessed via EDC gateway uses minimum-necessary scoping — only fields required for the briefing are retrieved. PHI is not stored in the briefing text; subject identifiers are used only for query tracking. Production deployments should enable Bedrock Guardrails for an additional PHI-scrubbing layer.

## Customer responsibilities

Computer-system validation for the intended use, IdP integration and role mapping, connector validation to CTMS/eTMF/EDC, Bedrock Guardrail configuration, and ClinOps sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
