# Regulatory & Compliance Framework — Pharmacovigilance ICSR Intake Agent

This agent operates inside a GVP, ICH E2B(R3), 21 CFR Part 11, and model-risk
control envelope. It is a **decision-support** system: it parses, extracts, codes,
and drafts; a qualified PV Medical Reviewer confirms causality, seriousness, and
authorizes submission.

## Context of use (FDA/EMA good-AI principles, Jan 2026)

| Question | Answer for this agent |
|---|---|
| What does the model do? | Parses AE source records, extracts E2B fields, codes to MedDRA/WHODrug, assesses seriousness, drafts ICSR narrative. |
| What does it NOT do? | Determine final causality; finalize/submit an ICSR; make clinical decisions. |
| Who is accountable? | The PV Medical Reviewer who confirms seriousness, causality, and authorizes submission. |
| What is the risk if wrong? | A defective narrative is caught by grounding/quality checks + human review before submission. A missed SAR could delay a safety signal — mitigated by seriousness heuristics + reviewer gate. |

Controls are proportional to that risk: grounding verification, PHI check, required-element
check, prompt version pinning, audit trail, and a framework-enforced HITL gate.

## GVP Module VI — Pharmacovigilance reporting

| GVP requirement | Agent implementation |
|---|---|
| 4 mandatory ICSR elements | `validity_check` node enforces identifiable patient, reporter, product, event |
| ICH E2A seriousness criteria | `seriousness_assessment` classifies all 6 criteria deterministically |
| 7-/15-day reporting clock | Computed from seriousness + expectedness; displayed prominently |
| E2B(R3) narrative elements | Required-element check in `quality_checker`; narrative template enforces who/what/when/seriousness/causality |
| Case retention | PostgresSaver + DynamoDB (product life + 10 years in prod) |

## ICH E2B(R3) data elements

The extracted fields map directly to ICH E2B(R3) data elements:

| E2B(R3) block | Fields | Source |
|---|---|---|
| D.1 Patient | age, sex, weight, history | `case_extractor` |
| D.2 Reporter | name, type, country | `case_extractor` |
| D.3 Drug | suspect_drug, dose, route, indication | `case_extractor` + `coder` (WHODrug) |
| D.4 Reaction | event_description, onset, outcome | `case_extractor` + `coder` (MedDRA PT/SOC) |
| D.5 Study | N/A (spontaneous workflow) | — |
| D.6 Seriousness | criteria, expectedness, clock | `seriousness_assessor` |
| D.7 Causality | causality_assessment | `seriousness_assessor` + reviewer gate |
| D.8 Narrative | narrative_text | `narrative_drafter` |

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry (actor, action, data sources, model used). Production sink is append-only (DynamoDB/QLDB).
- **Electronic signature linkage** — at the human gate, a verified reviewer identity (IdP `sub`, roles, signature meaning, timestamp) is bound to the approval.
- **Record integrity** — cases are versioned; the grounding report is attached to the record.
- **Access control** — RBAC via IdP roles (`PV_PROCESSOR`, `PV_MEDICAL_REVIEWER`); only a Medical Reviewer authorizes the safety DB write.

## PHI safeguards

Raw PII (SSN, NPI, full name in narrative) is checked before human review. A detected SSN
pattern triggers ESCALATE — the narrative never advances to submission. In production, Bedrock
Guardrails add a PHI filter layer so content does not leave the AWS account.

## MedDRA and WHODrug licensing

Production use requires a licensed MedDRA browser (MSSO) and WHODrug dictionary (Uppsala).
Demo mode uses a small fixture table with realistic coded terms to keep the pipeline fully
offline. Coding via the MCP gateway (meddra.code_term / whodrug.code_drug) routes to the
licensed service in production.

## Model risk (SR 11-7 posture)

The narrative prompt is part of the model. It is registered and hash-pinned in
`governance/prompt_manifest.json`; CI fails on un-bumped drift. The eval harness
(`governance/evals`) is the ongoing performance check.

## Customer responsibility

Computer-system validation for the intended use, IdP integration and role mapping,
connector validation to Argus/Veeva Safety/MedDRA/WHODrug, Bedrock Guardrail
configuration, and submission authorization procedures. This accelerator provides
the control *design*; the customer operationalizes and validates it.
