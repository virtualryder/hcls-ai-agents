# Third-Party Risk Management — Due Diligence Packet
### HCLS AI Agent Suite — Vendor Assessment Reference

> This packet is prepared for the SI's response to customer TPRM / vendor due-diligence questionnaires. It addresses the standard assessment categories for an AI tool that processes health and clinical data in a life-sciences environment. Where a response depends on the specific deployment configuration, the recommended answer is provided; the customer's procurement team should verify against the actual deployment.

---

## 1. Deployment Architecture and Data Residency

**Q: Where is our data processed?**

A: In the customer's own AWS account, in the customer's designated AWS region. The platform runs on Amazon Bedrock (inference), Amazon DynamoDB (audit trail), Amazon S3 (document storage), and supporting AWS services. No data is sent to the SI's infrastructure, to a shared multi-tenant environment, or to any non-AWS external service.

**Q: Does the SI or any third party have access to our PHI?**

A: During implementation and managed service engagements, SI engineers may have temporary, time-limited, role-scoped access to the customer's AWS account for deployment, configuration, and troubleshooting purposes. This access is governed by: (a) the customer's IAM role policies, which limit the SI to specific resources and actions; (b) SI access-management procedures including just-in-time access controls; (c) the engagement contract, which specifies that SI personnel do not access, retain, or process PHI beyond what is technically necessary for the agreed services.

If a managed service is in scope, a Business Associate Agreement (BAA) and Data Processing Addendum (DPA) are executed between the SI and the customer before any access to PHI-containing environments is granted.

**Q: What AWS regions are supported?**

A: The platform is deployed in the customer's chosen AWS region, subject to Amazon Bedrock AgentCore and Bedrock model availability in that region. Amazon Bedrock is currently available in US East, US West, EU West, EU Central, AP Southeast, and AP Northeast regions, among others. The customer should confirm current regional availability with their AWS account team for their specific model and service selections.

---

## 2. HIPAA Compliance

**Q: Does the SI provide a HIPAA Business Associate Agreement?**

A: Yes, for managed service engagements where the SI has access to PHI-containing environments. The BAA is executed before any managed service work begins. For POC and Pilot engagements where the SI delivers software and configuration services but does not have ongoing access to PHI, the appropriate agreement is negotiated based on the specific access scope.

**Q: Does AWS provide a BAA for the services used in this platform?**

A: Yes. Amazon Web Services provides a Business Associate Agreement for Amazon Bedrock, Amazon DynamoDB, Amazon S3, AWS KMS, Amazon Cognito, Amazon CloudWatch, AWS CloudTrail, and AWS Step Functions, among other services used in this platform. Customers must execute the AWS BAA through their AWS account console before processing PHI on these services. The AWS BAA is a standard, non-negotiated agreement; its terms are available at aws.amazon.com/compliance/hipaa-eligible-services-reference/.

**Q: How is PHI protected in transit and at rest?**

A: **At rest:** All data stores — DynamoDB, S3, and CloudWatch Logs — are encrypted at rest using AWS KMS with a customer-managed key. The customer controls the KMS key policy and can revoke access at any time.

**In transit:** All communication between platform components uses TLS 1.2 minimum. Bedrock is accessed via a VPC Interface Endpoint (PrivateLink), ensuring that inference traffic does not traverse the public internet.

**In prompts:** PHI is masked by the NER-based PHI masker before any data enters a Bedrock prompt. The LLM processes pseudonymized data; the pseudonym-to-identifier mapping table is held under the customer's KMS key.

---

## 3. Security Certifications and Controls

**Q: What is the SOC 2 posture for this platform?**

A: The AWS infrastructure underlying the platform (Bedrock, DynamoDB, S3, KMS, Cognito, CloudWatch) is covered by AWS's SOC 2 Type II certification. AWS SOC 2 reports are available in the AWS Artifact portal under the customer's AWS account.

The SI's own professional services organization maintains SOC 2 Type II certification covering its development and managed service delivery processes. The SI's current SOC 2 report is available to customers under NDA upon request.

The customer-deployed software accelerator itself is not SOC 2 certified as a standalone product — it is an accelerator deployed in the customer's account, and the customer's security posture governs. The SI provides the security configuration (IAM roles, KMS key policy, VPC configuration, Guardrail settings) and a configuration review report as part of the Pilot engagement.

**Q: What is the HITRUST posture?**

A: The AWS infrastructure is HITRUST CSF certified. The SI's managed service organization is pursuing HITRUST r2 certification; current certification status is available from the SI's TPRM team. Customers with a HITRUST requirement should confirm the current certification scope and timeline with the SI engagement team.

**Q: Has the platform undergone penetration testing?**

A: Penetration testing of the deployed environment is a standard deliverable for the production Pilot engagement, scoped and delivered before go-live. The penetration test is conducted by the SI's security practice or a customer-nominated third party, per the customer's TPRM policy. The test scope covers the deployed CloudFormation stack (network, IAM, application, and data layers), the MCP authorization gateway, and the API surfaces exposed to end users. Findings and remediation status are documented in the security review report.

---

## 4. AI Model Governance

**Q: Which AI model is used?**

A: The platform uses Anthropic's Claude model family, accessed via Amazon Bedrock in the customer's AWS account. The specific Claude model version (e.g., Claude 3.5 Sonnet, Claude 3 Haiku) is selected at deployment and pinned in the CloudFormation configuration. Model version changes require SI change-control review and eval harness regression before deployment.

**Q: Does the AI model train on our data?**

A: No. Amazon Bedrock does not use customer inference data to train or improve foundation models by default. This is governed by the AWS service terms and applies to all Bedrock model invocations. Anthropic, as a subprocessor of AWS, does not receive customer inference data from in-account Bedrock deployments. The customer should confirm this with their AWS account team and review the AWS data-privacy documentation relevant to Bedrock.

**Q: How is prompt drift and model behavior change managed?**

A: The prompt version registry (`governance/prompt_registry.py`) hash-pins all prompts at deployment. CI fails on unreviewed prompt changes. Model version updates are gated behind: (a) SI review of the Bedrock model release notes, (b) regression of the eval harness against the new model version using reviewed golden artifacts, (c) customer notification and approval (in managed service engagements), and (d) documented change-control record. This satisfies the SR 11-7-style model-risk management expectation that a model change is treated as a significant model change requiring review.

**Q: What are the model's documented failure modes?**

A: Documented failure modes and their mitigations include:

| Failure mode | Mitigation |
|---|---|
| Hallucinated claim (entity/figure not in source corpus) | Grounding verification catches before human review |
| Prohibited language (promotional, off-label, absolute claim) | Prohibited-language gate (deterministic) + Bedrock Guardrails |
| Structural incompleteness (missing E2B fields, CTD section elements) | Structural eval harness checks before HITL queue |
| Demographic bias in cohort recommendations | Fairness check (representativeness flags) before output surfaces |
| Prompt injection (adversarial instruction smuggled via input) | Red-team suite tests; gateway authorization cannot be changed by prompt content |
| PHI exfiltration via model output | PHI masking pre-prompt + Bedrock Guardrails PHI denial policy |

---

## 5. Subprocessors

**Q: Who are the subprocessors for this platform?**

A: In the in-account deployment topology, the subprocessors are AWS services operated by Amazon Web Services, Inc. (and its applicable regional entities). Key AWS services and their data-processing roles:

| AWS Service | Data processed |
|---|---|
| Amazon Bedrock | Pseudonymized prompt content and model responses (inference) |
| Amazon DynamoDB | Append-only audit trail records (PHI-masked) |
| Amazon S3 | Finalized regulated documents (encrypted); audit snapshots |
| AWS KMS | Encryption key management (no plaintext data) |
| Amazon Cognito | User authentication tokens (no PHI) |
| Amazon CloudWatch | Operational metrics and logs (PHI-masked) |
| AWS CloudTrail | API-level audit records (no PHI payload content) |
| AWS Step Functions | Workflow state (PHI-masked) |

The SI does not introduce additional AI-layer subprocessors in the in-account deployment topology. If the SI's managed service involves remote access tools, those are disclosed separately in the DPA.

**Q: Are subprocessors outside the EU used for EU customer data?**

A: The platform can be deployed in AWS EU regions (EU West, EU Central), ensuring that data does not leave the EU geographic perimeter. Amazon Web Services EMEA SARL (Luxembourg) serves as the relevant AWS entity for EU-based processing. The customer should confirm their specific GDPR/Schrems II posture with their DPO and AWS account team.

---

## 6. Incident Response and Notification

**Q: What is the SI's incident notification obligation?**

A: If the SI discovers a security incident involving the customer's data or environment, the SI will notify the customer's designated security contact within the timeframe required by the engagement contract and applicable law (typically 24–72 hours of confirmed discovery, depending on jurisdiction). The SI's incident response procedures are documented in the SI's SOC 2 report and available for review under NDA.

**Q: What is the incident response procedure for this platform?**

A: The platform's operational incident response runbook is at `runbooks/INCIDENT-RESPONSE.md`. For managed service engagements, the SI's on-call team initiates the P1 response procedure immediately upon detection and coordinates with the customer's CISO and designated contact. All incident actions are documented in an append-only incident record (separate from the production audit trail) for post-incident review.

---

## 7. Right to Audit and Compliance Evidence

**Q: Do we have the right to audit the platform?**

A: Because the platform is deployed in the customer's own AWS account, the customer has inherent audit access to every AWS service log, CloudTrail event, DynamoDB audit record, and CloudWatch metric. The customer does not require SI permission or involvement to review any aspect of the platform's operational record. This is a structural advantage of the in-account deployment model over SaaS alternatives.

The SI's managed service activities that occur outside the customer's AWS account (e.g., the SI's own change management, release management, and access control processes) are subject to the customer's right-to-audit clause in the managed service contract, exercisable annually with reasonable notice.

**Q: What compliance evidence can the SI provide?**

A: Available compliance evidence includes: SI SOC 2 Type II report (under NDA); SI HITRUST certification scope letter; penetration test report and remediation evidence (from Pilot engagement); validation package (RTM, IQ evidence, OQ/PQ templates) from the Pilot; prompt change-control log; eval harness regression results; and configuration review report (IAM, KMS, VPC, Guardrail settings).
