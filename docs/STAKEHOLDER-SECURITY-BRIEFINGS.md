# Stakeholder Security Briefings
### HCLS AI Agent Suite — Per-Stakeholder Security and Compliance Narrative

> These briefings are written for SI sales executives and solution architects preparing for stakeholder meetings at a life-sciences customer. Each section covers what the stakeholder cares about, how to approach them, and why the security architecture matters specifically to their function and accountability.

---

## 1. CIO / CTO

### What they care about
Total cost of ownership, speed to value, platform consolidation, vendor lock-in risk, talent leverage, and the ability to scale a successful pilot to enterprise without rebuilding. They want AI that works within their existing AWS investment — not a separate SaaS contract with a new vendor to manage.

### How to approach them
Lead with the platform story, not the agent story. The eight agents are applications; the governed platform is the durable investment. The same gateway, audit trail, identity layer, and governance controls that govern Agent 01 govern all eight — the cost of adding each additional agent falls sharply once the platform is operational.

Frame it as **API modernization**: the MCP authorization gateway brings governed, auditable access to systems of record (Veeva, Argus, Medidata, TrackWise) that have historically been accessible only via thick-client or FTP. This is infrastructure value, independent of AI.

### Why security matters to them specifically
The CIO/CTO is accountable if an AI agent exfiltrates PHI, produces a hallucinated submission that reaches a health authority, or creates an unauthorized ICSR entry that triggers a regulatory action. The platform's security architecture is their liability shield:

- **In-account Bedrock inference**: PHI never leaves their AWS account to an external API endpoint. The data governance perimeter is maintained.
- **MCP authorization gateway (deny-by-default)**: An agent cannot call any system it is not explicitly granted. A compromised agent credential does not result in data exfiltration because the tool it would need to exfiltrate data is not in its grant list.
- **No standing service accounts**: Short-lived scoped tokens are minted per call via AgentCore Identity. There is no long-lived credential for an attacker to steal from a config file.
- **IaC-driven deployment**: The CloudFormation quick-deploy produces a reproducible, version-controlled environment. There is no snowflake infrastructure or manual configuration drift.

**Key message**: "This is not a third-party AI service that processes your clinical data externally. It is infrastructure you own, deployed in your account, governed by your policies."

---

## 2. CISO

### What they care about
Data residency and egress controls, identity and access management rigor, the blast radius of a compromise, auditability, third-party and supply-chain risk, and the ability to demonstrate controls to a regulator or external auditor.

### How to approach them
Go deep, early. CISOs are accustomed to vendors glossing over security architecture; a detailed technical briefing on the authorization model, token lifecycle, PHI masking, and audit trail will differentiate the engagement. Request a dedicated security architecture review session before or alongside the business case.

Prepare to address: model behavior (can the LLM be prompted to exfiltrate data?), prompt injection, supply-chain risk in the Python dependencies, and the security of the audit trail itself.

### Why security matters to them specifically
The CISO's mandate is to prevent unauthorized access, detect anomalies, and maintain an auditable control record. Every element of the platform is designed against those goals:

**PHI masking (pre-prompt)**
NER-based entity recognition replaces patient identifiers, case-linkable fields, and dates of birth with stable pseudonyms before any content enters an LLM prompt. Even if an adversary succeeded in extracting the model's context window, they would receive pseudonymized text, not identified PHI. The mapping table is held under a customer-managed KMS key.

**Deny-by-default authorization with least-privilege intersection**
The gateway's authorization decision is `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`. This is not a whitelist on one axis — it is an intersection on two axes simultaneously. A compromised PV agent credential cannot reach the RIM. A privileged user acting through the wrong agent is still denied. The blast radius of any single compromise is bounded to exactly the tools that agent is granted for exactly the roles the user holds.

**Short-lived scoped tokens**
AgentCore Identity mints a credential scoped to exactly one tool call, valid for a short window. There are no standing service accounts, no API keys in config files, and no long-lived IAM users. The STS call is logged; the token cannot be reused.

**Tamper-evident audit trail**
The DynamoDB audit table is governed by an IAM policy that denies `UpdateItem` and `DeleteItem` on the audit partition key. Point-in-Time Recovery is enabled. The audit record cannot be modified or deleted post-write — including by the application service role. For the highest-assurance scenarios (e-signature chains), QLDB provides cryptographic provenance.

**Bedrock Guardrails (model-level content control)**
Guardrails run on every Bedrock call, enforcing PHI denial policies at the model layer — a second defense after PHI masking at the gateway layer. If a prompt were constructed to elicit PHI from the model's in-context window, Guardrails would block the response.

**Red team suite**
`governance/redteam/` includes prompt injection tests, PHI exfiltration scenarios, and authorization bypass attempts. These run in CI. The CISO can review the adversarial test coverage as part of their due diligence.

**Network posture**
All agent compute runs in private subnets. Bedrock is accessed via a VPC Interface Endpoint — traffic does not traverse the internet. No inbound public access; no EC2 instances with public IPs. WAF can be placed at the ALB/CloudFront layer in production.

**Key message**: "The authorization model is deny-by-default at two intersecting axes, enforced at the gateway — not in agent code that can be bypassed. The PHI masker runs before the prompt; Guardrails run inside Bedrock. There are two independent PHI controls before data reaches a model response."

---

## 3. Chief Medical Officer (CMO)

### What they care about
Patient safety, scientific integrity, clinical accuracy, and the risk that AI-generated content influences clinical decisions or reaches patients in a form that has not been reviewed by a qualified physician.

### How to approach them
The CMO's concern is less about data security and more about **epistemic safety**: can the AI produce a clinically incorrect recommendation that is acted upon? Frame the platform's design around the principle that "AI drafts; qualified professionals decide." The HITL gate is not a UX feature — it is a safety control.

### Why security matters to them specifically
The CMO is accountable for the scientific validity and patient-safety implications of clinical and medical affairs outputs. The platform's security controls map directly to those concerns:

**Grounding verification (hallucination prevention)**
Every number, endpoint, dose, and adverse-event term in a regulated draft must be traceable to a source document in the grounding corpus. A hallucinated efficacy figure or an invented safety signal does not survive the grounding check — it fails before a physician or reviewer sees it. This is the primary clinical accuracy control.

**Prohibited-language gate**
The compliance gate checks for and blocks promotional claims ("cure," "best-in-class," "completely safe"), absolute efficacy claims, and off-label content. This is enforced deterministically, not by the LLM — the LLM cannot talk its way around a regex-based prohibition.

**Bedrock Guardrails (topic filter)**
Guardrails are configured at the stack level with topic filters appropriate to the medical context. In production, these include medical advice boundaries, off-label promotion boundaries, and crisis escalation rules.

**HITL gate (framework-enforced)**
The LangGraph `interrupt_before` on the finalize node cannot be removed by a configuration change — it is in the graph definition, tested in CI (`governance/tests/test_hitl_gates.py`). A physician or qualified reviewer must actively approve before any write to a system of record occurs. The AI's role is advisory.

**Scope boundaries per agent**
Agent 08 (Medical Affairs / MSL Copilot) has access only to HCP records (`crm.get_hcp`), approved documents (`dms.get_document`), and MLR submission (`mlr.submit_for_review`). It has no access to patient data, clinical trial data, or safety databases. Scope is enforced at the gateway, not by documentation.

**Key message**: "The AI never reaches a patient or a health authority without a named physician or qualified professional making an active, recorded approval decision. The grounding check means a hallucinated clinical figure fails before a reviewer sees it."

---

## 4. Head of Regulatory Affairs

### What they care about
Submission quality and consistency, defensibility of AI-assisted content in a health-authority review, the risk of a hallucinated or unsupported claim in a submission, and whether the tool can be validated under GxP/computer-system-assurance procedures.

### How to approach them
This stakeholder will be the most technically rigorous on the regulatory compliance question. Bring the compliance documentation (`01-regulatory-writing-agent/docs/regulatory-compliance.md`, `governance/README.md`). Be prepared to walk through the 21 CFR Part 11 control mapping, the grounding verification architecture, and the customer's validation responsibility.

### Why security matters to them specifically
The Head of Regulatory Affairs is accountable for the integrity of every submission artifact. A data-integrity finding in a health-authority inspection is a program-stopping event.

**Grounding verification (ALCOA+ Accurate)**
The grounding check is the primary data-integrity control. It enforces that every figure, term, and assertion in a regulated draft is attributable to a specific source document in the grounding corpus. This satisfies the GxP ALCOA+ "Accurate" and "Attributable" principles at the agent level.

**21 CFR Part 11 audit trail**
Every node in the regulatory writing graph appends a timestamped, attributable record: actor (IdP sub and roles), action (node name), data sources (grounding corpus identifiers), model version (Bedrock model ID), and outcome. The record is written to an append-only store. This is the audit trail required by 21 CFR Part 11 for electronic records.

**Electronic signature linkage**
At the HITL gate, the Regulatory Approver's identity (IdP sub, role `REGULATORY_APPROVER`, timestamp, signature meaning) is cryptographically bound to the approval record. The AI-generated draft is not separable from the approval record in the audit trail.

**Prompt version registry (model-risk change control)**
When a prompt is changed — even a small wording adjustment — the prompt registry detects the hash drift and CI fails. The Regulatory Affairs team can request a prompt change log as change-control evidence.

**Computer-system validation pathway**
The platform provides the control design. The customer validates it. The documentation in `01-regulatory-writing-agent/docs/regulatory-compliance.md` is structured to support IQ/OQ/PQ documentation. The eval harness provides performance-qualification evidence over golden test cases.

**Key message**: "Every claim in a draft the AI produces is traceable to a source document before a human sees it. The approver's identity and the draft state are bound together in a tamper-evident record. The tool is designed to be validated under GxP/CSA procedures."

---

## 5. Head of Pharmacovigilance / Drug Safety

### What they care about
Case processing throughput and quality, 15-day expedited reporting windows, MedDRA coding accuracy, E2B(R3) structural completeness, duplicate case detection, and the risk that an AI error results in a missed regulatory report — a potentially criminal failure.

### How to approach them
PV/Drug Safety leaders are acutely aware that adverse-event reporting errors can result in Warning Letters, consent decrees, and personal liability. Approach with quantified risk reduction, not capability hype. Emphasize that the AI handles triage and drafting; a Medical Reviewer with documented authority still submits.

### Why security matters to them specifically
The safety of the PV agent's architecture is the safety of the pharmacovigilance process.

**Role-gated submission tool**
`safety.submit_report` — the irreversible E2B submission — is in the tool registry with `high_risk=True`. It can only be called by the `02-pharmacovigilance` agent. Even within that agent, it requires the acting user to hold the `PV_MEDICAL_REVIEWER` role (the most senior PV role). A `PV_PROCESSOR` cannot trigger a submission, regardless of what the agent is asked to do. This mirrors the real-world two-tier PV review process.

**E2B(R3) structural completeness (eval harness)**
The governance eval harness includes CIOMS/E2B(R3) structural completeness checks against golden test ICSR cases. These run in CI. A prompt or model change that degrades the structural completeness of an ICSR draft causes CI to fail before the change reaches production.

**MedDRA coding validation**
The `meddra.code_term` connector validates proposed terms against the live MedDRA dictionary version. Confidence scores are surfaced to the Medical Reviewer. Low-confidence codes are flagged, not silently accepted.

**Duplicate detection**
`safety.search_duplicates` runs against the safety database before any case draft is created. The duplicate search result is included in the Medical Reviewer's queue, not just used to filter silently.

**Audit trail for case provenance**
Every ICSR case processed by the agent carries a lineage record: which source document triggered triage, which duplicate search was run, which MedDRA terms were proposed, and which reviewer approved the submission. This supports retrospective case-quality audits and regulatory inspection readiness.

**PHI masking in PV context**
Patient identifiers in case narratives are pseudonymized before entering the LLM prompt. The pseudonymization is stable (the same patient identifier produces the same pseudonym within a session), so cross-case linkage for duplicate detection is preserved without exposing PHI to the model.

**Key message**: "The Medical Reviewer role is the only role that can authorize a submission. The AI processes and drafts; a named, credentialed human submits. The E2B structural completeness checks run before the case reaches the reviewer — you catch structural gaps before the 15-day window, not after."

---

## 6. Head of Quality / QA

### What they care about
CAPA on-time closure rates, inspection readiness, root-cause consistency, complaint handling timeliness, and — increasingly — validation of any computerized system used in a GMP/GCP environment under 21 CFR Part 11 and the FDA QMSR (effective February 2026).

### How to approach them
Quality leaders have extensive experience with computerized system validation and are skeptical of any tool that has not been through a formal validation process. Acknowledge this directly. The platform provides the control design and the validation documentation inputs; the customer performs the validation.

### Why security matters to them specifically
A Quality leader signing off on a CAPA closure or complaint investigation outcome is personally accountable for the quality system record. The platform's security architecture protects the integrity of those records.

**CAPA closure gate (role-gated irreversible action)**
`qms.close_capa` has `high_risk=True` and is restricted to the `QUALIFIED_PERSON` role. A Quality Reviewer who can draft a CAPA cannot close it — the same segregation of duties that exists in a paper-based QMS is enforced technically at the gateway.

**Append-only CAPA and complaint records**
The audit trail for every agent interaction with the QMS is written to an append-only DynamoDB table. The quality record cannot be modified after the fact. This is directly relevant to FDA inspection readiness: if an inspector asks "what did the AI do to this CAPA record and when?", the answer is in an immutable, timestamped record.

**Root-cause similarity search**
The `qms.search_similar` tool searches for similar historical CAPAs before a new investigation is drafted. This promotes consistency — a key QMSR expectation — and surfaces precedent that a human investigator might have missed.

**FDA QMSR (Feb 2026) posture**
The QMSR updates 21 CFR Part 820 to align with ISO 13485. Agent 05's workflow is designed against the QMSR's expectations for complaint handling (prompt intake, documented investigation, corrective action), and the Quality / CAPA agent's tool set maps to the QMSR process flow: receive complaint → investigate → identify root cause → draft CAPA → close CAPA (QP only).

**Computer-system validation pathway**
The platform's control structure (audit trail, e-signature, access control, validation documentation) is designed to support IQ/OQ/PQ under 21 CFR Part 11 and GAMP 5 Category 4/5. The eval harness provides performance-qualification test evidence over documented golden cases.

**Key message**: "The Qualified Person is the only role that can close a CAPA in the system. Every agent interaction with your QMS is in an immutable audit record that will satisfy an FDA inspector. We provide the validation documentation inputs; your QA team runs the validation."

---

## 7. Head of Clinical Operations

### What they care about
TMF inspection readiness, EDC query resolution time, site performance and enrollment velocity, and the risk of a TMF gap becoming a clinical hold or GCP finding in an inspection.

### How to approach them
Clinical Operations leaders are operationally focused and data-hungry. Lead with the operational efficiency story (continuous TMF completeness vs. periodic inspection sprint; automated EDC queries vs. manual CRA review) and back it with the compliance story when they ask "can we actually use this?"

### Why security matters to them specifically
An EDC query that modifies subject data, or a TMF document that is filed or amended, is a GCP data-integrity event. The security architecture governs the integrity of these actions.

**Scope-limited EDC write**
The `edc.create_query` tool (the only write tool for Agent 03) creates an EDC query — a reversible, audit-trailed action — not a subject data modification. The agent cannot modify subject data directly. This boundary is enforced at the gateway.

**Clinops access model**
The `CLINOPS_LEAD` role can create EDC queries, retrieve subject data, and check TMF completeness. They cannot modify RIM records, write safety cases, or create CAPAs. The intersection model ensures that Clinical Operations' tools are scoped to Clinical Operations' data.

**GCP audit trail for subject data queries**
Every `edc.get_subject_data` and `edc.create_query` call is logged with the acting user's identity, the query parameters (PHI-masked), and the outcome. This supports GCP inspection readiness: an inspector can see exactly which subject data was accessed, by whom (role), and when.

**TMF completeness as continuous monitoring, not periodic inspection**
`etmf.get_completeness` is a read tool with no approval gate — it can run continuously on a scheduled basis to produce a live TMF gap view. This shifts TMF readiness from a pre-inspection sprint (high risk, high cost) to a continuous operational posture.

**Key message**: "The agent cannot modify subject data — it can create a query for site review. Every access to EDC data is logged. TMF gaps are visible continuously, not just before an inspection."

---

## 8. Chief Privacy Officer / DPO

### What they care about
HIPAA compliance, GDPR compliance, data residency, data minimization, data subject rights, lawful basis for AI processing, and whether the AI tool constitutes automated decision-making with legal or similarly significant effects (GDPR Article 22).

### How to approach them
The CPO/DPO is often the gatekeeper for any AI tool that processes personal or health data. A thorough, accurate privacy briefing early in the engagement avoids a late-stage veto. Be honest about what data the platform processes and what it does not — this stakeholder will detect overstatements.

### Why security matters to them specifically
The CPO/DPO is personally accountable (GDPR Article 39) for ensuring that data protection is built into processing by design and by default. The platform's architecture is a direct implementation of privacy-by-design principles.

**Data residency — in-account Bedrock**
The patient and clinical data processed by the agents never leaves the customer's AWS account or their designated AWS region. Bedrock is accessed via a VPC Interface Endpoint; there is no path from the agent to an external inference API. The CPO/DPO can verify data residency through CloudTrail — every Bedrock API call is logged with the region endpoint.

**PHI masking (data minimization at the prompt layer)**
Identifiers are replaced with stable pseudonyms before any data enters an LLM prompt. The LLM processes pseudonymized data; the mapping table is held under a customer-managed KMS key that the CPO/DPO's team controls. This is a technical implementation of GDPR's data minimization principle at the point of AI processing.

**Minimum-necessary access (HIPAA Security Rule)**
The gateway's least-privilege intersection model ensures that agents access only the data fields their specific tool requires, not full patient records. A cohort-query tool returns aggregate counts, not individual records, unless the specific tool definition requires subject-level data — and that level of access requires a higher-privilege role.

**No automated decision-making with legal effects**
GDPR Article 22 requires specific safeguards for automated decisions with legal or similarly significant effects. The platform's HITL gate means that no consequential decision — an adverse-event report, a regulatory submission, a CAPA closure — is taken without a named human making an active, recorded approval. The AI provides a recommendation; the human decides. This removes the platform from the GDPR Article 22 high-risk category for the functions it supports.

**Data subject rights**
Audit records contain pseudonymized identifiers. The mapping table (pseudonym → real identifier) is held under a customer-controlled KMS key. The customer can fulfill erasure requests by deleting the mapping table entry without modifying the audit trail (which remains intact for compliance purposes but becomes non-linkable to the data subject).

**Subprocessors**
The platform's subprocessors are: AWS (Bedrock, DynamoDB, S3, KMS, Cognito, CloudWatch). There are no additional AI-layer subprocessors in the in-account deployment topology. See `offerings/TPRM-DUE-DILIGENCE-PACKET.md` for the full subprocessor list and HIPAA BAA status.

**EU AI Act (deployer obligations)**
For EU-based customers, the CPO/DPO should be involved in the EU AI Act deployer assessment under Article 16. The platform's documentation (context of use per agent, technical controls, human oversight mechanism, audit logs) provides the technical input for that assessment.

**Key message**: "PHI never leaves your AWS account. The platform processes pseudonymized data in the LLM layer. Humans make every consequential decision — the platform does not meet the GDPR Article 22 automated-decision-making threshold for the functions it supports."

---

## 9. Head of Medical Affairs / MSL Leadership

### What they care about
HCP relationship quality, scientific exchange accuracy, MLR cycle time, off-label risk, and the ability to deploy scientific resources effectively in a competitive field environment.

### How to approach them
Medical Affairs leaders want tools that make their MSLs more scientifically credible and responsive without creating off-label risk. The pitch is "always on-label, always grounded, always evidence-backed" — with the MLR routing built in so the right content flows to the right process.

### Why security matters to them specifically
Medical Affairs operates at the intersection of scientific communication, commercial pressure, and regulatory restriction. An off-label promotional communication from an MSL is a compliance event.

**Off-label technical guardrail**
The Medical Affairs agent has access to approved documents (`dms.get_document`) and HCP records (`crm.get_hcp`). It does not have access to clinical trial data, unapproved compound information, or study data beyond what is in the approved document repository. The gateway enforces this scope boundary. Off-label promotion risk is reduced technically, not just through training.

**Bedrock Guardrails — topic filter**
The Guardrail configuration at the stack level includes a topic filter for off-label and promotional content. Even if an MSL asks the agent "what can I tell an HCP about the unapproved indication?", the Guardrail blocks the response.

**MLR routing (audit-trailed write)**
The `mlr.submit_for_review` tool — the only write tool for Agent 08 — routes content to the MLR review queue with a full audit trail. The MSL does not bypass MLR; the agent makes routing easier. The `MEDICAL_AFFAIRS_APPROVER` role is required to trigger MLR submission; a standard `MSL` role cannot.

**HCP interaction audit trail**
Every agent interaction in an MSL session is logged with the HCP identifier (pseudonymized), the scientific question, the evidence sources retrieved, and the response generated. This supports the Medical Affairs compliance obligation to maintain records of scientific exchange.

**Key message**: "The off-label guardrail is technical, not procedural — the agent does not have access to unapproved content, and Guardrails blocks off-label responses at the model layer. Every MSL interaction is in an audit trail for your compliance team."

---

## 10. Procurement / Third-Party Risk Management (TPRM)

### What they care about
Vendor risk classification, HIPAA Business Associate Agreement status, SOC 2 / HITRUST certification posture, data-flow documentation, subprocessors, penetration test evidence, incident response SLAs, and contractual right to audit.

### How to approach them
Procurement and TPRM teams follow a structured due-diligence process. Provide the TPRM packet early (`offerings/TPRM-DUE-DILIGENCE-PACKET.md`) and offer a working session to walk through it. The most common TPRM delay is waiting for a complete response to a standard questionnaire.

### Why security matters to them specifically
TPRM's mandate is to ensure that every vendor or technology in the organization's supply chain meets its data-security and compliance obligations. The in-account deployment model materially changes the TPRM risk picture.

**In-account deployment (reduced third-party risk surface)**
Because the platform runs in the customer's own AWS account, the SI is not a subprocessor of PHI in the traditional sense. The customer is the data controller and data processor; the SI provides the software and implementation services. This simplifies the TPRM assessment: the customer assesses AWS (already assessed) and the SI's implementation services, not a SaaS vendor processing their PHI externally.

**AWS subprocessor coverage**
AWS provides a HIPAA BAA covering Bedrock, DynamoDB, S3, KMS, Cognito, and CloudWatch. AWS SOC 2 Type II and HITRUST CSF certifications are current. These are available in the AWS Artifact portal.

**SI obligations**
The SI's obligations in this deployment are: deliver and maintain the software accelerator; perform implementation and integration services; not retain access to customer PHI post-engagement unless contracted for managed services. If a managed service is in scope, a BAA and data-processing addendum (DPA) with the SI are required.

**Penetration test**
A penetration test against the deployed environment is a standard engagement deliverable before production go-live. Evidence of the test and remediation status is provided in the engagement's security documentation package.

**Right to audit**
The deployment is in the customer's AWS account. The customer can inspect every CloudTrail log, every DynamoDB audit record, and every Bedrock Guardrail invocation without SI involvement. The right to audit is inherent in the architecture.

**Key message**: "Your PHI stays in your AWS account. AWS provides the BAA. The SI's role is implementation, not data processing. You have full visibility into every agent action in your own CloudTrail logs."

---

## 11. IRB / Ethics Perspective

### What they care about (for engagements involving clinical research subjects)
Informed consent scope, data-use agreements, de-identification standards, algorithmic fairness, and whether AI-assisted decisions about research subjects are adequately disclosed in consent forms.

### How to approach them
IRB and ethics involvement is most relevant for Agent 04 (Site Selection & Patient Matching) and Agent 07 (RWE / HEOR), where the platform queries real-world data to identify potential research subjects or analyze patient outcomes. Engage IRB/ethics early if the deployment involves identifiable patient data for research purposes.

### Why security matters to them specifically
IRBs are concerned that AI tools do not introduce undisclosed risks to research subjects, that data use is within the scope of the consent obtained, and that algorithmic recommendations do not systematically disadvantage protected subgroups.

**De-identification as a prerequisite**
Agent 04 and Agent 07 are designed to operate on de-identified data (Safe Harbor or Expert Determination standard under 45 CFR 164.514). The RWD connector returns de-identified data; the gateway policy does not permit a query that returns identified data to these agents. Identifiable patient matching for study enrollment requires a separate, validated workflow with explicit IRB approval.

**Algorithmic fairness checks**
`governance/fairness/test_cohort_representativeness.py` flags material demographic under-representation in proposed cohorts against FDA Diversity Action Plan benchmarks. This check runs as part of the governance layer and surfaces to the clinical team before a cohort is finalized. It does not make the decision; it surfaces information for the human epidemiologist or clinical lead to act on.

**Consent scope**
The platform does not assess whether a specific data use is within the scope of a patient's consent — that assessment is the IRB's and the customer's responsibility. The platform ensures that data access is technically limited to what the authorized tool allows; the customer is responsible for ensuring the authorized tool access is within the scope of applicable consents and data-use agreements.

**Disclosure in consent forms**
For clinical trials that use Agent 03 (Clinical Trial Ops) or Agent 06 (Protocol Design) in study execution, IRBs may require disclosure of AI-assisted tools in the consent form. The platform's context-of-use documentation per agent is designed to support that disclosure: it describes exactly what the AI does, what it does not do, and who is accountable for decisions.

**Key message**: "The RWD agents operate on de-identified data by design. The fairness check surfaces demographic representation gaps before a cohort is finalized — that decision remains with your clinical team. We provide the documentation to support IRB disclosure of AI-assisted tools in consent forms."
