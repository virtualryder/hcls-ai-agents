# HCLS AI Agent Suite — Managed Service
### Consulting Offering — Scope, Deliverables, and Engagement Structure

---

## Offering Summary

An ongoing managed service engagement in which the SI operates the HCLS AI Agent Suite platform on behalf of the customer. The SI provides infrastructure management, model and prompt change control, observability and alerting, HITL queue support, incident response, and periodic platform reviews. The customer retains ownership of the AWS account, the data, and all regulated decisions; the SI operates the platform machinery that enables those decisions.

This offering is appropriate for customers who have completed a production Pilot and want to scale to additional agents without building a permanent internal platform operations team, or for customers whose IT organization does not have AI/ML platform expertise in-house.

---

## Scope

### Continuous operations

**Infrastructure management:**
- CloudFormation stack monitoring and update management; Terraform state management if applicable
- KMS key rotation and audit
- DynamoDB and S3 capacity monitoring; PITR verification
- VPC and security group review on a quarterly basis
- AWS cost optimization (right-sizing, Reserved Instance / Savings Plan recommendations)

**Observability and alerting:**
- CloudWatch dashboard maintenance and alarm tuning
- HITL queue depth monitoring and escalation (queue depth alarm → SI ops team → customer designated contact)
- Model invocation error rate monitoring
- Bedrock Guardrail trigger rate monitoring (unexpected spike in PHI detections or off-label blocks is an anomaly signal)
- Monthly operations report: invocation volumes, HITL approval latency, error rates, cost trend

**Model and prompt change control:**
- Prompt version registry management: all prompt changes submitted via pull request, reviewed by SI domain architect, hash-pinned, regression-tested against eval harness before deployment
- Bedrock model version management: model upgrade notices reviewed; customer notified of proposed model changes; evaluation run before upgrade
- Connector dependency management: vendor API version changes absorbed by the SI connector layer

**HITL queue support (Tier 1):**
- HITL queue monitoring; escalation to customer's functional team if queue depth exceeds agreed SLA
- Queue management tooling support; user access troubleshooting
- Not in scope: the SI does not perform functional review of agent output content — that is the customer's regulated responsibility

**Incident response (SI responsibility):**
- P1 (production outage, data-integrity risk): SI on-call response per SLA; see `runbooks/INCIDENT-RESPONSE.md`
- P2 (degraded function, no data risk): response within agreed SLA; root cause and remediation within one business day
- Incident documentation and post-incident review report

**Model degradation response:**
- Monthly eval harness execution against current production prompts and model; comparison to baseline
- Anomaly detection in production quality metrics (grounding accuracy, structural completeness scores)
- Degradation response per `runbooks/MODEL-DEGRADATION-RESPONSE.md`

### Platform evolution (included in managed service)

**Quarterly platform review:**
- Assessment of new AWS Bedrock capabilities (new models, Guardrail features, AgentCore capabilities) for applicability
- Regulatory landscape review: FDA/EMA guidance updates, QMSR implementation, EU AI Act developments — with recommendation on platform impact

**Annual security review:**
- Configuration review of the deployed stack (IAM, KMS, VPC, Guardrails, DynamoDB audit policy)
- Penetration test coordination (test execution priced separately)
- SOC 2 evidence package contribution for customer's own audit reporting

---

## What Is Not in Scope (Customer Responsibility)

- All regulated functional decisions (HITL approval, submission authorization, CAPA closure, ICSR submission) — these are always the customer's qualified professionals' responsibility
- Computer-system validation for new agents or major version updates
- IdP administration (role mapping, user provisioning in the customer IdP)
- Data sourcing and connector-level data quality (the SI maintains the connector; the customer maintains the source system)
- Training and change management for end users

---

## Team and Governance

**SI managed service team:**
- Platform Operations Lead (primary customer contact, escalation point)
- AI/ML Platform Engineer (on-call rotation for P1/P2)
- Security Operations Engineer (quarterly review, incident support)
- Life Sciences Domain Advisor (prompt change review, model evaluation)

**Governance cadence:**
- Weekly: HITL queue and infrastructure health check (async, dashboard-based)
- Monthly: operations report delivered to customer designated contact
- Quarterly: platform review meeting with customer IT lead, functional sponsor, and SI team
- Annually: security review, contract renewal, scope adjustment

---

## SLA Structure

| Priority | Definition | Initial response | Resolution target |
|---|---|---|---|
| P1 | Production outage or confirmed data-integrity risk | 30 minutes (24/7) | 4 hours |
| P2 | Degraded function, no data-integrity risk | 2 hours (business hours) | Next business day |
| P3 | Non-urgent request or enhancement | Next business day | Agreed per ticket |
| P4 | Informational / reporting | 5 business days | Per schedule |

SLAs are measured from customer notification or SI detection (whichever is first) to initial response. Resolution targets are for restoration of service, not root-cause completion.

---

## Pricing Approach

Monthly recurring fee based on: number of agents under management, invocation volume tier, and SLA tier selected (standard business hours vs. 24/7 P1 coverage). Setup fee covers onboarding from the customer's pilot environment, runbook adaptation, and managed service tooling configuration. Annual contract with quarterly review and scope adjustment option.

Pricing is structured as a recurring service fee, not a per-invocation API fee — predictable for the customer's budget planning. AWS infrastructure costs remain the customer's responsibility and pass through at cost (or can be managed under the customer's enterprise AWS agreement).

---

## Transition and Exit

At any time, the customer can elect to in-source the platform operations. The SI will provide a transition period (typically 60–90 days) during which the internal team shadows SI operations, runbooks are transferred, and access is migrated. The customer retains all code, infrastructure as code, runbooks, audit trails, and prompt registries. There is no proprietary lock-in beyond the SI's implementation services.
