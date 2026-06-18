# Shared Responsibility Matrix
### AWS · Systems Integrator · Life Sciences Institution

> **For procurement, CISO, and QA audiences.** When a regulated institution deploys AI agents that touch PHI and produce submission-grade artifacts, the question "who is responsible for what?" must have a written answer. This matrix is that answer — covering security, compliance, operations, and model governance across the three parties.
>
> This is a reference matrix for the HCLS AI Agent Suite deployed on AWS. Adapt the SI column to reflect your specific MSA and the institution column to reflect their validated system boundary.

---

## How to Read This Matrix

| Symbol | Meaning |
|---|---|
| **OWNS** | This party is the primary responsible party — they perform the work, hold the accountability, and are the named party in audits or incidents |
| **CONTRIBUTES** | This party has a defined supporting role — they provide inputs, tooling, or approvals but are not the accountable party |
| **REVIEWS / APPROVES** | This party must formally approve or acknowledge before the action is complete |
| **NOT IN SCOPE** | This party has no obligation in this area under the standard engagement model |

---

## Section 1 — Infrastructure & Platform Security

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| Physical security of data centers | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |
| Hypervisor and host OS security | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |
| AWS service availability and SLAs (Bedrock, DynamoDB, Step Functions, Cognito) | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |
| VPC design, subnet segmentation, security groups | CONTRIBUTES (Well-Architected guidance) | **OWNS** | REVIEWS / APPROVES |
| Network ACLs and VPC flow logs | CONTRIBUTES (service) | **OWNS** | REVIEWS / APPROVES |
| IAM roles and policies for AWS services | CONTRIBUTES (IAM service) | **OWNS** (CloudFormation-defined roles) | REVIEWS / APPROVES |
| KMS key creation and rotation policy | CONTRIBUTES (KMS service) | **OWNS** (default policy) | REVIEWS / APPROVES (key ownership) |
| AWS CloudTrail enablement and retention | CONTRIBUTES (service) | **OWNS** (configuration) | REVIEWS / APPROVES |
| Container image security (Fargate task definitions) | CONTRIBUTES (ECR scanning) | **OWNS** | NOT IN SCOPE |
| Patch management for OS/runtime (Fargate) | **OWNS** (managed compute) | NOT IN SCOPE | NOT IN SCOPE |
| Bedrock model endpoint security | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |
| AgentCore Gateway + Identity service security | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |

---

## Section 2 — Application & Data Security

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| MCP authorization gateway (deny-by-default policy) | CONTRIBUTES (AgentCore Identity service) | **OWNS** (policy.py, AGENT_TOOL_GRANTS) | REVIEWS / APPROVES |
| JWT token verification and IdP federation (Cognito) | CONTRIBUTES (Cognito service) | **OWNS** (configuration) | REVIEWS / APPROVES (IdP integration) |
| PHI masking at audit boundary | NOT IN SCOPE | **OWNS** (phi.py, Safe Harbor implementation) | REVIEWS / APPROVES |
| Prompt injection prevention | NOT IN SCOPE | **OWNS** (red team test suite, grounding) | REVIEWS / APPROVES |
| Grounding verification (no hallucinated claims in output) | NOT IN SCOPE | **OWNS** (governance/grounding.py) | REVIEWS / APPROVES |
| Encryption at rest (DynamoDB, S3, QLDB) | CONTRIBUTES (KMS-backed encryption) | **OWNS** (enabled by default in CloudFormation) | REVIEWS / APPROVES |
| Encryption in transit (TLS) | **OWNS** (Bedrock, API Gateway enforce TLS) | **OWNS** (service-to-service calls) | NOT IN SCOPE |
| Secret management (API keys, connector credentials) | CONTRIBUTES (Secrets Manager service) | **OWNS** (configuration, rotation schedule) | CONTRIBUTES (provides credentials) |
| Application penetration testing | NOT IN SCOPE | **OWNS** (pre-go-live; scope per SOW) | REVIEWS / APPROVES (scope and findings) |
| Vulnerability scanning of application code | NOT IN SCOPE | **OWNS** (CI pipeline) | NOT IN SCOPE |
| Data classification and PHI inventory | NOT IN SCOPE | CONTRIBUTES (fixture tagging, connector documentation) | **OWNS** |

---

## Section 3 — Compliance & Regulatory

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| HIPAA Business Associate Agreement (BAA) | **OWNS** (AWS BAA covers HIPAA-eligible services) | NOT IN SCOPE | REVIEWS / APPROVES (executes BAA with AWS) |
| 21 CFR Part 11 — audit trail implementation | NOT IN SCOPE | **OWNS** (append-only DynamoDB + QLDB; tamper-evident design) | REVIEWS / APPROVES |
| 21 CFR Part 11 — e-signature binding | NOT IN SCOPE | **OWNS** (HITL reviewer identity recorded at approval) | REVIEWS / APPROVES (validates per their SOP) |
| 21 CFR Part 11 — system validation (CSV/GAMP) | NOT IN SCOPE | CONTRIBUTES (IQ/OQ/PQ documentation templates) | **OWNS** (executes and signs validation) |
| GxP computer system assurance (CSA) scoping | NOT IN SCOPE | CONTRIBUTES (CSA scoping guide) | **OWNS** |
| GVP / ICH E2B(R3) compliance (Agent 02 PV) | NOT IN SCOPE | **OWNS** (ICSR structure, field mapping) | REVIEWS / APPROVES |
| FDA Diversity Action Plan (Agent 04) | NOT IN SCOPE | **OWNS** (cohort representativeness check) | REVIEWS / APPROVES |
| ISO 13485 / EU MDR (Agent 05 Quality) | NOT IN SCOPE | CONTRIBUTES (CAPA structure) | **OWNS** |
| SOC 2 Type II (AWS infrastructure layer) | **OWNS** (AWS holds SOC 2 reports; available via AWS Artifact) | NOT IN SCOPE | REVIEWS / APPROVES (requests AWS Artifact reports) |
| SOC 2 (SI engagement delivery) | NOT IN SCOPE | **OWNS** (SI's own SOC 2 if applicable) | REVIEWS / APPROVES |
| Model risk governance (SR 11-7 equivalent for HCLS) | NOT IN SCOPE | **OWNS** (prompt versioning, eval harness, grounding) | REVIEWS / APPROVES |
| Third-party model risk assessment (LLM) | NOT IN SCOPE | CONTRIBUTES (Anthropic model card, TPRM packet) | **OWNS** (executes TPRM review) |

---

## Section 4 — Operations & Incident Response

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| AWS service incident response (e.g., Bedrock outage) | **OWNS** | NOT IN SCOPE | NOT IN SCOPE |
| Application incident detection and response | NOT IN SCOPE | **OWNS** (during Pilot/Managed Service) | CONTRIBUTES (reports observed anomalies) |
| HITL queue monitoring and escalation | NOT IN SCOPE | **OWNS** (runbook; SLA targets) | CONTRIBUTES (domain advisor escalation path) |
| Model degradation detection and response | NOT IN SCOPE | **OWNS** (eval canaries, runbook) | REVIEWS / APPROVES (approves model rollback) |
| Disaster recovery execution | NOT IN SCOPE | **OWNS** (DR runbook; tested procedures) | REVIEWS / APPROVES (signs off on RTO/RPO targets) |
| Business continuity planning | NOT IN SCOPE | CONTRIBUTES (DR runbook, architecture) | **OWNS** |
| Security incident — notification to institution | NOT IN SCOPE | **OWNS** (contractual; timeframe per SOW) | REVIEWS / APPROVES |
| Security incident — regulatory notification (FDA, HHS OCR) | NOT IN SCOPE | CONTRIBUTES (root cause, timeline) | **OWNS** |
| Change management (model updates, prompt changes) | NOT IN SCOPE | **OWNS** (prompt registry; CI gate; change notification) | REVIEWS / APPROVES |
| Audit trail preservation during incidents | NOT IN SCOPE | **OWNS** (preservation-before-action principle) | REVIEWS / APPROVES |

---

## Section 5 — Human-in-the-Loop (HITL) Governance

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| HITL gate technical enforcement | NOT IN SCOPE | **OWNS** (LangGraph interrupt; cannot be bypassed by model) | NOT IN SCOPE |
| HITL gate SLA definition | NOT IN SCOPE | CONTRIBUTES (default SLAs in runbook) | **OWNS** (approves SLAs for their workflows) |
| Qualified reviewer assignment (e.g., PV Medical Reviewer, QP, Regulatory Approver) | NOT IN SCOPE | NOT IN SCOPE | **OWNS** |
| Reviewer training and qualification | NOT IN SCOPE | CONTRIBUTES (workflow documentation) | **OWNS** |
| Approved artifact custody | NOT IN SCOPE | NOT IN SCOPE | **OWNS** |
| HITL queue operations during Managed Service | NOT IN SCOPE | **OWNS** | CONTRIBUTES (domain advisors available for escalation) |

---

## Section 6 — Vendor and Model Governance

| Control | AWS | Systems Integrator | Institution |
|---|---|---|---|
| Anthropic (Claude) model training and safety | NOT IN SCOPE (Anthropic responsibility) | NOT IN SCOPE | NOT IN SCOPE |
| Anthropic BAA / data processing agreement | NOT IN SCOPE | CONTRIBUTES (Anthropic commercial terms) | **OWNS** (executes agreement with Anthropic) |
| Bedrock model access and terms of service | **OWNS** (Bedrock service) | NOT IN SCOPE | **OWNS** (customer AWS account; accepts Bedrock model access terms) |
| Connector vendor agreements (Veeva, Medidata, TrackWise) | NOT IN SCOPE | NOT IN SCOPE | **OWNS** |
| Connector API credentials and rotation | NOT IN SCOPE | CONTRIBUTES (Secrets Manager configuration) | **OWNS** (provides and manages credentials) |
| TPRM review of SI | NOT IN SCOPE | CONTRIBUTES (TPRM Due Diligence Packet) | **OWNS** (executes TPRM assessment) |

---

## Frequently Asked Questions

**Q: Who is responsible if an ICSR narrative contains a hallucinated value?**
A: The SI owns the grounding verification implementation (`governance/grounding.py`). The institution owns the validation of that implementation as part of CSV/CSA. The qualified reviewer (PV Medical Reviewer) owns the decision to approve the artifact. All three parties have a defined role; the technical control is the grounding check.

**Q: Who owns the AWS account?**
A: The institution owns the AWS account (customer-managed). The SI manages resources within it during the engagement. At Managed Service handover, account access is scoped to the SI's operational role; the institution retains root/owner access.

**Q: If AWS Bedrock has an outage, who is responsible for the SLA to the institution?**
A: AWS owns the Bedrock service SLA. The SI's application SLA (if offered in a Managed Service) is conditioned on the underlying AWS service SLA; the SOW should explicitly state this dependency and the escalation path.

**Q: Who handles FDA inspection readiness for the audit trail?**
A: The institution owns the regulated system and the inspection response. The SI owns the implementation of the audit trail and provides the technical documentation for inspection. The AWS BAA and AWS Artifact SOC 2 reports support the infrastructure layer.

---

*Related: `offerings/TPRM-DUE-DILIGENCE-PACKET.md`, `docs/AWS-ACCOUNT-PREREQUISITES.md`, `docs/WELL-ARCHITECTED-REVIEW.md`, `offerings/SOW-TEMPLATE.md`*
