# Regulatory & Compliance Framework — RWE & HEOR Agent

This agent operates inside an FDA RWE framework, GDPR research exemption, ISPOR good-practices, and 21 CFR Part 11 control envelope.
It is a **decision-support** system: it retrieves, synthesizes, and drafts; qualified health economists and medical reviewers decide and authorize.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Retrieves de-identified real-world data and published literature, synthesizes evidence by research question, and drafts an evidence summary for payer submissions. |
| What does it NOT do? | Access patient-level PHI; submit evidence packages autonomously; make cost-effectiveness conclusions without reviewer sign-off. |
| Who is accountable? | The qualified health economist or medical reviewer who approves the evidence summary. |
| What is the risk if wrong? | An unsupported claim in a payer dossier is caught by grounding verification and reviewer check before submission. |

## FDA RWE Framework (2018 guidance + 2021 guidance series)

FDA has published extensive guidance on the use of real-world evidence in regulatory decision-making. This agent implements key FDA RWE expectations:

- **Fit-for-purpose data source transparency** — the data source, query parameters, de-identification method, and retrieval timestamp are recorded in the audit trail for every RWD query.
- **Aggregate-only access** — the gateway enforces aggregate-count-only RWD queries, consistent with FDA's expectation that patient-level data used in regulatory submissions be subject to appropriate de-identification and access controls.
- **Reproducibility** — the evidence synthesis is grounded to the retrieved corpus in state; every number in the summary is traceable to a source, supporting the reproducibility requirement.

## GDPR Article 89 — research exemption and de-identification

Where RWD originates from EU patient populations, GDPR Article 89 permits processing for scientific research purposes subject to appropriate safeguards:

- **Data minimization** — only aggregate counts are transmitted to the agent; patient-level records remain at the source system.
- **De-identification** — the gateway connector contract requires the RWD platform to apply de-identification before responding; the phi_note field in the cohort result is a required structural element checked by the quality gate.
- **Technical and organizational measures** — Bedrock Guardrails provide an additional PHI-detection layer in production; the audit trail records all data access.

## ISPOR RWE good practices

ISPOR Task Force reports on real-world evidence define transparency, reproducibility, and appropriate uncertainty quantification as core requirements. The agent's grounding verification directly supports ISPOR transparency requirements: every quantitative claim in the synthesis is traceable to a retrieved source in state.

## AMCP Format and HTA dossier standards

The quality gate enforces the presence of required structural sections for AMCP Format submissions (clinical evidence summary, economic evidence summary, budget impact) and HTA dossier sections. Missing sections trigger a revision before the evidence summary reaches the reviewer.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry. Production sink is append-only (DynamoDB/QLDB).
- **Authorization linkage** — at the human gate, a verified reviewer identity (IdP `sub`, role, timestamp) is bound to the approval before the evidence package is saved to the dossier system.
- **Record integrity** — evidence summaries are versioned; grounding reports are attached to each record.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`. Demo mode is fully deterministic, supporting validation evidence generation. The absolute-claim gate blocks unsupported conclusions ("definitively superior", "guaranteed cost savings") that would undermine the scientific integrity of payer submissions.

## Customer responsibilities

RWD platform de-identification validation, IdP integration and reviewer role mapping, dossier system connector validation, Bedrock Guardrail configuration, and health-economist sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it.
