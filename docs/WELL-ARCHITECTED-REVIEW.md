# AWS Well-Architected + Generative AI Lens Review Mapping
### Pillar-by-pillar positioning for the HCLS AI Agent Suite

> **For Solutions Architects and SI technical leads.** AWS SAs run a Well-Architected Framework Review (WAFR) on most enterprise engagements — often as a prerequisite for MAP funding approval. This document maps the HCLS Agent Suite's design decisions to each WAF pillar and to the Generative AI Lens, so you can answer WAFR questions without starting from scratch.
>
> Use this as prep for the WAFR session, not as a substitute for it. The actual WAFR produces a findings report; this is the architecture evidence that satisfies the high-risk questions.

---

## WAF Pillar 1 — Operational Excellence

**Goal:** Run and monitor systems to deliver business value and continually improve processes.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you determine what your priorities are? | Platform maturity ladder documents four levels; per-agent ADRs record scope decisions | `README.md` — Maturity Ladder |
| How do you structure your organization to support your workload? | HITL gates enforce human accountability; roles defined per-workflow (PV Processor, Regulatory Approver, QP, etc.) | `runbooks/README.md` |
| How do you evolve operations? | Prompt versioning + registry; CI fails on un-bumped prompt drift; eval harness catches regressions | `governance/prompt_registry.py`, `governance/evals/` |
| How do you understand workload health? | CloudWatch dashboards; HITL queue depth monitoring; model degradation runbook | `runbooks/MODEL-DEGRADATION-RESPONSE.md` |
| How do you manage workload and operations events? | Incident response runbook with P1/P2/P3 SLAs and role-based escalation | `runbooks/INCIDENT-RESPONSE.md` |
| How do you mitigate deployment risks? | `EXTRACT_MODE=demo` isolates test runs; CloudFormation enables rollback; per-stage CI gates | `docs/DEPLOYMENT-HANDBOOK.md` |

**WAFR finding risk:** Low. The suite has runbooks, role definitions, and automated regression testing — more than most enterprise AI deployments.

---

## WAF Pillar 2 — Security

**Goal:** Protect information, systems, and assets while delivering business value.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you securely operate your workload? | Deny-by-default MCP gateway; all tool calls require verified identity + role entitlement | `platform_core/hcls_agent_platform/mcp_gateway/policy.py` |
| How do you manage identities for people and machines? | Amazon Cognito IdP federation; JWT verification at gateway; no long-lived agent credentials | `platform_core/hcls_agent_platform/auth.py` |
| How do you manage permissions? | AGENT_TOOL_GRANTS ∩ ROLE_ENTITLEMENTS — agent can never exceed human's permissions | `platform_core/hcls_agent_platform/mcp_gateway/policy.py` |
| How do you detect and investigate security events? | Append-only DynamoDB audit trail + QLDB for Part 11; CloudTrail for AWS API calls | `platform_core/hcls_agent_platform/mcp_gateway/audit.py` |
| How do you protect your network resources? | VPC + private subnets; AgentCore Gateway as the sole external-facing endpoint; no direct DB exposure | `infra/cloudformation/` |
| How do you protect your compute resources? | Fargate task isolation; no SSH; image scanning in CI | `infra/cloudformation/ecs-task.yaml` |
| How do you classify your data? | PHI masking at audit boundary (Safe Harbor); fixture vs. live connector separation | `platform_core/hcls_agent_platform/phi.py` |
| How do you protect your data at rest? | KMS encryption on DynamoDB, S3, and QLDB; customer-managed keys configurable | `infra/cloudformation/` |
| How do you protect your data in transit? | TLS 1.2+ enforced; no plaintext inter-service calls; Secrets Manager for credentials | `platform_core/hcls_agent_platform/secrets.py` |
| How do you anticipate, respond to, and recover from incidents? | Incident response runbook; preservation-before-action principle; forensics log collection procedure | `runbooks/INCIDENT-RESPONSE.md` |

**WAFR finding risk:** Low–medium. KMS key rotation policy and VPC flow log retention are items to confirm per deployment; the defaults are set in CloudFormation but customers sometimes override.

---

## WAF Pillar 3 — Reliability

**Goal:** Ensure a workload performs its intended function correctly and consistently.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you manage service quotas and constraints? | Service quota pre-flight in prerequisites checklist; Bedrock model access verified before deploy | `docs/AWS-ACCOUNT-PREREQUISITES.md` |
| How do you plan your network topology? | Multi-AZ Fargate; DynamoDB global tables optional for DR; VPC endpoints for Bedrock/S3 | `infra/cloudformation/` |
| How do you design your workload service architecture? | Each agent is stateless compute + durable LangGraph state in DynamoDB; Step Functions for retry | `aws-native-reference/` |
| How do you mitigate single points of failure? | HITL queue is DynamoDB-backed (multi-AZ); Step Functions handles retries with exponential backoff | `aws-native-reference/` |
| How do you test reliability? | 503 tests covering agent graphs, gateway enforcement, connector modes; DR runbook with tested procedures | `runbooks/DR-RUNBOOK.md` |
| How do you plan for disaster recovery? | DR runbook: RTO/RPO definitions, PITR on DynamoDB, cross-region backup strategy | `runbooks/DR-RUNBOOK.md` |

**WAFR finding risk:** Medium. Multi-region active-active is not implemented by default (cost-prohibitive for most HCLS POCs); document the DR posture explicitly for CISO/QA audiences.

---

## WAF Pillar 4 — Performance Efficiency

**Goal:** Use IT and computing resources efficiently to meet system requirements.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you select appropriate resources? | Claude claude-sonnet-4-6 default (balanced capability/cost); Haiku for classification steps; configurable via `llm_factory.py` | `platform_core/hcls_agent_platform/llm_factory.py` |
| How do you select and use storage? | DynamoDB for agent state (low latency); S3 for document artifacts; no oversized primary DB | Per-agent `agent/persistence.py` |
| How do you monitor your resources? | CloudWatch metrics + custom HITL queue depth alarm; X-Ray tracing via OpenTelemetry | `platform_core/hcls_agent_platform/tracing.py` |
| How do you use trade-offs to improve performance? | Grounding check runs after draft (not inline) to avoid adding to critical path latency | Per-agent `agent/graph.py` |

**WAFR finding risk:** Low. Model selection is configurable; cost and latency benchmarks should be captured during POC and documented before Pilot.

---

## WAF Pillar 5 — Cost Optimization

**Goal:** Run systems at the lowest price point while delivering business value.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you implement cloud financial management? | Per-agent cost tagging (AgentId, TenantId, Environment) in CloudFormation; cost by agent queryable | `infra/cloudformation/` |
| How do you govern usage? | Bedrock Guardrails limits token throughput; AgentCore quotas by tenant | `platform_core/hcls_agent_platform/llm_factory.py` |
| How do you decommission resources? | `EXTRACT_MODE=demo` uses zero Bedrock tokens; fixture connectors generate zero external API cost | `platform_core/hcls_agent_platform/connectors/fixtures.py` |
| How do you evaluate cost when making architecture decisions? | TCO model documents Bedrock inference, Step Functions, DynamoDB, AgentCore per-agent cost estimates | `offerings/TCO-MODEL.md` |

**WAFR finding risk:** Low–medium. Savings Plans / Reserved capacity for Fargate is not pre-configured (appropriate for POC/Pilot; should be addressed at Managed Service stage).

---

## WAF Pillar 6 — Sustainability

**Goal:** Minimize the environmental impact of running cloud workloads.

| WAFR Question (abbreviated) | How the Suite addresses it | Evidence in repo |
|---|---|---|
| How do you select AWS Regions? | Default us-east-1 (high renewable energy mix); region is a CloudFormation parameter | `infra/cloudformation/` |
| How do you take advantage of software and architecture patterns? | Serverless-first (Lambda, Fargate, Step Functions, DynamoDB); no always-on EC2 by default | `aws-native-reference/` |
| How do you minimize waste? | Demo mode uses fixture connectors — zero inference tokens; Fargate scales to zero | `platform_core/hcls_agent_platform/connectors/fixtures.py` |

**WAFR finding risk:** Low. Sustainability is rarely a blocker in HCLS enterprise deals but is increasingly a procurement checklist item.

---

## Generative AI Lens — Key Dimensions

The AWS Generative AI Lens (published 2024) adds AI-specific best practices on top of the six WAF pillars. The high-risk questions for a regulated HCLS deployment:

### GenAI Lens: Responsible AI

| Lens Question | How the Suite addresses it |
|---|---|
| How do you ensure model outputs are accurate and reliable? | Deterministic grounding verification (`governance/grounding.py`) — every claim traced to source; CI eval harness with golden artifacts |
| How do you manage bias and fairness? | FDA Diversity Action Plan compliance (`governance/fairness/test_cohort_representativeness.py`); demographic under-representation flagged before site/patient output is approved |
| How do you enable human oversight? | Framework-enforced HITL gates (not documented policy) — high-risk tools interrupt the LangGraph graph; cannot be bypassed by model output (`governance/tests/test_hitl_gates.py`) |
| How do you handle sensitive data? | PHI masking at audit boundary (HIPAA Safe Harbor 18 identifiers); grounding check prevents re-injection of masked data |

### GenAI Lens: Model Selection and Management

| Lens Question | How the Suite addresses it |
|---|---|
| How do you select foundation models? | `llm_factory.py` abstracts model selection; Bedrock Guardrails applied to all production paths; configurable per agent role |
| How do you manage model versions and changes? | Prompt version pinning (`governance/prompt_registry.py`); eval harness catches behavioral regressions; ADR-001 documents orchestration stance |
| How do you monitor model performance over time? | Model degradation runbook (`runbooks/MODEL-DEGRADATION-RESPONSE.md`); eval canaries (`governance/_canary.py`); grounding regression tracked in CI |

### GenAI Lens: Security for AI Workloads

| Lens Question | How the Suite addresses it |
|---|---|
| How do you prevent prompt injection? | Red team test suite (`governance/redteam/test_prompt_injection.py`) — injected instructions cannot change authorization; grounding catches smuggled facts |
| How do you control access to foundation models? | Bedrock IAM resource policies; AgentCore Identity scopes per-agent model access; no direct API key in application code |
| How do you audit AI interactions? | Append-only DynamoDB audit trail — every tool call, decision, and HITL approval recorded with user_sub, agent_id, timestamp, and outcome |

### GenAI Lens: Cost and Performance

| Lens Question | How the Suite addresses it |
|---|---|
| How do you optimize inference costs? | Model tiering (Sonnet for drafting, Haiku for classification); demo mode for offline testing; Bedrock token budgets configurable |
| How do you benchmark and test performance? | 503 automated tests; demo path runs full workflow without API spend; latency measured per graph node via OpenTelemetry |

---

## WAFR Session Logistics

**Who should attend:**
- SI: Technical Lead, Solution Architect
- Customer: Cloud Architect, CISO (or delegate), platform owner
- AWS: HCLS SA (required for MAP funding validation)

**Typical duration:** 2–3 hours for the six pillars; 1 additional hour for GenAI Lens if the AWS SA requests it.

**Output:** AWS-generated findings report (High / Medium / Low risk items); MAP credit eligibility is partially gated on completing the WAFR and addressing High-risk findings.

**Prepare:** Bring this document + the deployment architecture diagram from `docs/SUITE-ARCHITECTURE.md` + the prerequisites checklist from `docs/AWS-ACCOUNT-PREREQUISITES.md`.

---

*Related: `docs/AWS-ACCOUNT-PREREQUISITES.md`, `docs/SHARED-RESPONSIBILITY-MATRIX.md`, `docs/AWS-FUNDING-AND-GTM.md`*
