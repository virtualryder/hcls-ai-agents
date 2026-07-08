# GDPR / EU data-protection annex — HCLS Life Sciences AI Agent Suite

**Scope & honesty.** Several agents in this suite face EU-regulated processes — pharmacovigilance
(EudraVigilance / EMA), clinical trial operations (EU CTR / CTIS), and RWE/HEOR over EU real-world
data. This annex maps the EU General Data Protection Regulation (**GDPR**, Regulation (EU) 2016/679)
and adjacent EU rules to the platform's controls, and points to the companion
[`DPIA-TEMPLATE.md`](DPIA-TEMPLATE.md). It is **not legal advice and not a compliance attestation** —
it is a reference for the customer's Data Protection Officer and counsel, who own the determination.
This repo is a reference accelerator, not a certified product.

## Roles and lawful basis

| GDPR concept | Article | How it lands here |
|---|---|---|
| Controller vs processor | Art. 4, 28 | The customer (sponsor/CRO/marketing-authorization holder) is **controller**; where a deploying SI or AWS processes on their behalf, a **Art. 28 data-processing agreement** governs. The agents are tools operated within the controller's account. |
| Lawful basis | Art. 6 | Typically legal obligation (PV reporting under GVP), public interest, or legitimate interest — customer determines and documents. The agents do not select a lawful basis. |
| Special-category (health) data | Art. 9 | Health/genetic data requires an Art. 9(2) condition (e.g., public-health / GVP obligation). PHI masking runs before any model/audit write; grounding + human gate reduce automated inference. |
| Automated decision-making | Art. 22 | Consequential decisions (case seriousness sign-off, submission, QP release) are **withheld from every agent** and require a named human — the agents assist, a person decides, satisfying the Art. 22 "not solely automated" requirement for these steps. |

## Data residency & international transfers (Chapter V)

- **EU-region deployment.** The reference architecture is region-parameterized; for EU controllers,
  deploy into an EU AWS Region (e.g., `eu-central-1`, `eu-west-1`) or **AWS European Sovereign Cloud**
  where the customer requires EU-operated infrastructure.
- **Model + NLP services.** Amazon Bedrock and (in the payer/provider sibling) Comprehend Medical are
  **regional** services reached over interface VPC endpoints (AWS PrivateLink); traffic stays on AWS
  private networking within the chosen Region. Confirm the specific model/service availability and the
  processing Region for the customer's EU deployment — model availability varies by Region.
- **Transfers outside the EEA.** If any processing or support touches a non-adequate country, the
  controller relies on an adequacy decision or **Standard Contractual Clauses (SCCs)** plus a transfer
  impact assessment. The agents do not themselves initiate cross-border transfers; connectors are
  scoped to the systems of record the controller configures.

## Data-subject rights (Chapter III)

Access, rectification, erasure, restriction, portability, and objection are **controller
obligations** fulfilled in the systems of record (Veeva/Argus/Medidata), not in the agents. The
append-only audit trail supports demonstrating *what an agent did* with personal data (accountability,
Art. 5(2)) but is **not** itself the record subject to erasure — WORM audit retention is a documented,
lawful-basis-backed retention the controller must reconcile with erasure requests (a standard tension
resolved by the controller's retention schedule, not by deleting audit evidence).

## DPIA (Art. 35)

Large-scale special-category processing and profiling generally **require a DPIA**. Use
[`DPIA-TEMPLATE.md`](DPIA-TEMPLATE.md); the platform supplies much of the evidence a DPIA needs
(data-flow diagram, masking, human-gate, audit, minimization).

## Adjacent EU rules to flag

- **EU AI Act.** Some HCLS uses may be high-risk; the human-in-the-loop, logging, and transparency
  posture here supports (does not satisfy) the Act's requirements — customer performs the AI Act
  conformity work.
- **EU CTR / CTIS** (clinical trials) and **GVP** (pharmacovigilance) impose their own data and
  reporting duties that sit alongside GDPR — mapped in the per-agent compliance docs.

## Customer-owned (not provided by this repo)

DPO appointment; ROPA (Art. 30 records); lawful-basis and Art. 9 condition selection; DPIA sign-off;
SCCs/transfer assessments; data-subject-rights fulfillment; EU-region and Sovereign-Cloud deployment
choices; EU AI Act conformity. See [`../assurance/README.md`](../assurance/README.md).
