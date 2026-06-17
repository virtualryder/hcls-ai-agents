# Regulatory & Compliance Framework — Protocol Design Agent

This agent operates inside an ICH E6/E8/E9, Common Rule, and 21 CFR Part 11 control envelope.
It is a **decision-support** system: it retrieves guidance and drafts sections; qualified medical reviewers decide and authorize.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Retrieves applicable guidance, estimates eligible patient feasibility, and drafts key protocol sections. |
| What does it NOT do? | Finalize or submit protocols; determine sample size without statistical review; make medical claims. |
| Who is accountable? | The qualified medical or clinical reviewer who approves the draft before it is stored or submitted. |
| What is the risk if wrong? | A defective protocol section is caught by structural/grounding checks and medical review before any IRB or authority submission. |

## ICH E6(R3) GCP — protocol content requirements

ICH E6(R3) Annex 1 specifies required protocol content. The agent's structural check enforces the presence of:

- **Primary and secondary endpoints** — endpoint section is required; the check flags its absence.
- **Eligibility criteria** — inclusion and exclusion criteria section is required.
- **Study schedule** — visit schedule and assessment timepoints section is required.
- **Medical reviewer note** — the draft must include a statement that qualified review and approval is required before finalization.

## ICH E8(R1) — quality by design

ICH E8(R1) emphasizes designing studies with the minimum necessary complexity to address the scientific question. The agent surfaces feasibility estimates early — before eligibility criteria are locked — to support evidence-based design decisions that reduce amendment risk.

## ICH E9(R1) — estimands framework

The endpoint section template references the estimand framework (population, variable, intercurrent events, population-level summary) introduced by ICH E9(R1). The guidance retrieval step surfaces E9(R1) when the study involves a confirmatory endpoint.

## 45 CFR 46 (Common Rule) — IRB review

For academic sponsors and federally funded studies, the Common Rule applies. The eligibility section template includes a capacity-to-consent criterion, and the reviewer note prompts the medical reviewer to confirm that IRB submission requirements have been assessed.

## First-in-human considerations

For Phase 1 FIH studies, the protocol checker enforces additional structural elements: a safety monitoring committee or data safety monitoring board section and a stopping rule or dose-escalation decision criteria section. These align with FDA's FIH guidance expectations.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry. Production sink is append-only (DynamoDB/QLDB).
- **Electronic authorization linkage** — at the human gate, a verified reviewer identity is bound to the approval before the protocol draft is saved to the DMS.
- **Record integrity** — drafts are versioned; the grounding report and guidance retrieval results are attached to the record.

## GxP data integrity (ALCOA+)

The grounding check enforces *Accurate*: every number in the protocol draft (enrollment estimates, assessment timepoints) must be traceable to the cohort estimate or guidance state. The absolute-claim gate blocks efficacy or safety guarantees ("100% effective", "completely safe") that would be inconsistent with GCP and promotional guidelines.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`. Demo mode is fully deterministic and requires no API key, supporting validation evidence generation.

## Customer responsibilities

Computer-system validation for the intended use, IdP integration and medical reviewer role mapping, DMS connector validation, Bedrock Guardrail configuration, and medical reviewer sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
