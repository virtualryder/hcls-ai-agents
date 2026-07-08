# Data Protection Impact Assessment (DPIA) — template

**GDPR Art. 35.** Complete one DPIA per EU-facing deployment/use before processing begins. This is a
**template for the controller's DPO to complete and sign** — it is not a completed DPIA, not legal
advice, and not a compliance attestation. Pre-filled cells describe what the *platform* provides; the
controller fills the deployment-specific columns and owns the conclusion. See
[`GDPR-EU-ANNEX.md`](GDPR-EU-ANNEX.md).

## 1. Identification

| Field | Entry |
|---|---|
| Processing / agent(s) | _e.g., 02 Pharmacovigilance ICSR intake_ |
| Controller | _customer legal entity_ |
| Processor(s) | _SI / AWS under Art. 28 DPA_ |
| DPO | _name / contact_ |
| Date / version | _._ |
| Lawful basis (Art. 6) + Art. 9 condition | _controller determines_ |

## 2. Necessity & proportionality

| Question | Platform contribution | Controller entry |
|---|---|---|
| Is the processing necessary for the purpose? | Agents are decision-support; consequential steps are human-gated | _justify necessity_ |
| Data minimization (Art. 5(1)(c)) | PHI/PII masking before model/audit; only registered tools may read data | _confirm fields processed_ |
| Storage limitation | Retention parameterized; WORM audit retention documented | _set retention schedule_ |
| Purpose limitation | Deny-by-default gateway binds tools to declared purpose | _state purpose_ |

## 3. Data flow

Attach the suite data-flow diagram ([`diagrams/hcls-gxp-data-flow.svg`](diagrams/hcls-gxp-data-flow.svg))
and mark: sources, special-category fields, the masking boundary, the human-gate, the audit/WORM sink,
and the processing Region. Note any cross-border transfer and its Chapter V mechanism.

## 4. Risks to data subjects & mitigations

| Risk | Inherent | Mitigation (platform) | Residual | Owner |
|---|---|---|---|---|
| Unlawful disclosure of health data | High | Masking before any write; deny-by-default; least-privilege intersection | _._ | Controller |
| Solely-automated decision (Art. 22) | High | Consequential actions withheld in code; named human approval (SoD, single-use) | _._ | Controller |
| Inaccurate output affecting a person | Med | Grounding/output-schema checks; human review | _._ | Controller |
| Excessive retention vs erasure duty | Med | Parameterized retention; audit-vs-erasure reconciliation documented | _._ | Controller |
| Cross-border transfer to non-adequate country | Varies | EU-Region/Sovereign-Cloud deploy; PrivateLink; SCCs where needed | _._ | Controller |
| Re-identification from logs | Med | Fail-closed masking; append-only audit holds masked records only | _._ | Controller |

## 5. Consultation & sign-off

DPO opinion; where residual risk remains high after mitigation, **prior consultation with the
supervisory authority (Art. 36)**. Record data-subject/representative consultation if applicable.

| Role | Name | Decision | Date |
|---|---|---|---|
| DPO | | Approve / Approve-with-conditions / Reject | |
| Controller sign-off | | | |

## 6. Review

DPIA is reviewed on material change (new data category, new Region, model change, purpose change) and
at a defined interval set by the controller.
