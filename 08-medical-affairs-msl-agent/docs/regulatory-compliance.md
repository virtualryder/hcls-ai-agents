# Regulatory & Compliance Framework — Medical Affairs MSL Agent

This agent operates inside an FDA promotional-regulations, PhRMA Code, Sunshine Act, and MLR review control envelope.
It is a **decision-support** system: it retrieves approved content and drafts within the approved indication; qualified medical affairs personnel authorize every HCP interaction.

## Context of use

| Question | Answer for this agent |
|---|---|
| What does the model do? | Retrieves approved clinical data and HCP profile, drafts a pre-call brief grounded in on-label approved documents only. |
| What does it NOT do? | Share off-label information; contact HCPs; make promotional claims; bypass MLR review. |
| Who is accountable? | The medical affairs approver who reviews and signs off before the MSL uses the brief. |
| What is the risk if wrong? | Off-label or promotional content in a brief is detected by the compliance gate and triggers immediate escalation — the brief is held, not released. |

## FDA promotional regulations (21 CFR 202 and 21 USC 333)

The FDA prohibits promotion of prescription drugs or devices for uses not in the approved labeling. This agent enforces this boundary technically:

- **Off-label detection gate** — a deterministic regex check runs on every draft. Any occurrence of off-label reference language (e.g., "off-label", "unapproved use", "not approved for") triggers immediate escalation and blocks release. This gate cannot be bypassed by the model.
- **Approved-content-only corpus** — the brief drafting node receives only documents retrieved from the MLR-approved content library as its source corpus. The grounding check verifies that all claims in the draft are traceable to those approved documents.
- **On-label framing** — the brief template instructs the model to frame all content within the approved indication and labeling only, and to direct off-label questions to the medical information team.

## PhRMA Code on Interactions with Healthcare Professionals

The PhRMA Code requires that scientific exchange be educational, non-promotional, and driven by legitimate scientific need. The agent enforces these principles:

- **Promotional language gate** — a deterministic regex check blocks superlative, comparative, or promotional claim language ("best-in-class", "game-changer", "superior to all", "market-leading") from appearing in any brief.
- **Scientific exchange framing** — the brief template is structured around the HCP's scientific interests, approved clinical data, and anticipated scientific questions — not sales messaging.

## Sunshine Act (42 USC 1320a-7h)

The Physician Payments Sunshine Act requires manufacturers to report transfers of value to covered recipients. The agent's finalize node logs the MSL interaction in the CRM system with a timestamp, HCP identifier, and brief reference, providing the data trail needed for Sunshine Act reporting.

## MLR review standards

Medical, Legal, and Regulatory review is the standard industry control for promotional and medical affairs content. This agent is designed to work within, not replace, the MLR process:

- **Pre-screening** — the compliance gate pre-screens every brief for off-label and promotional issues before the medical affairs approver review, reducing MLR burden to substantive scientific review.
- **Grounding report** — the grounding report is surfaced to the approver at the human gate, showing exactly which approved documents each claim is traceable to.
- **Versioning** — each brief version is recorded with its grounding report and compliance findings, providing a complete audit trail for MLR records.

## 21 CFR Part 11 controls

- **Audit trail** — every node appends a timestamped, attributable entry. Production sink is append-only (DynamoDB/QLDB).
- **Authorization linkage** — at the human gate, a verified medical affairs approver identity (IdP `sub`, role, timestamp, signature meaning) is bound to the release before the CRM interaction is logged.
- **Record integrity** — brief versions are immutable after approval; the grounding and compliance reports are attached.

## Model risk posture

Prompts are registered and hash-pinned in `governance/prompt_manifest.json`. The deterministic compliance gate (off-label, promotional) is not LLM-dependent and cannot be overridden by model output — it runs on the draft text after generation. Demo mode is fully deterministic, supporting validation evidence generation.

## Customer responsibilities

MLR review procedure integration, IdP integration and medical-affairs-approver role mapping, CRM connector validation (for HCP profile retrieval and interaction logging), MLR-approved content library connector validation, Bedrock Guardrail configuration, and medical-affairs sign-off procedures. This accelerator provides the control *design*; the customer operationalizes and validates it per their promotional compliance program.
