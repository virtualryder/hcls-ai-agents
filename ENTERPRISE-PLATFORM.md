# Enterprise Platform
### HCLS AI Agent Suite — Architecture, Compliance, and Governance Story

> **An AI agent suite that a life-sciences enterprise can actually deploy is not primarily a model story. It is an API modernization, authorization, identity, and compliance-by-design story. The eight agents in this suite are the application layer above a platform that would need to exist regardless of what agents run on top of it.**

---

## 1. The Platform Problem in Life Sciences

Life-sciences organizations have accumulated deep, high-fidelity systems of record over decades — Veeva Vault RIM, Argus Safety, Medidata Rave, TrackWise, Veeva Vault eTMF, claims and registry databases, CRM. These systems are authoritative, validated, and expensive to change. They were not designed for agent-accessible APIs; many expose SOAP, proprietary REST, or file-based interfaces.

At the same time, every function in a regulated life-sciences organization operates under overlapping compliance frameworks — 21 CFR Part 11, HIPAA, GxP (GCP/GLP/GMP), GVP/ICH E2B(R3), FDA QMSR (effective February 2026), EU AI Act (phased implementation), GDPR, and FDA/EMA Good Machine Learning Practices (January 2026). An AI agent that touches any of these systems inherits all of those obligations.

The platform in this suite solves both problems. It provides:

1. A **governed front door** (the MCP authorization gateway) that abstracts vendor APIs, enforces least-privilege access, requires human approval for irreversible actions, and produces a tamper-evident audit trail
2. A **federated identity layer** that connects enterprise IdP roles to per-tool entitlements, so the authorization model is driven by the human's real access rights — not a shared service account
3. A **compliance-by-design substrate** that embeds HIPAA, Part 11, GxP, and model-risk controls at the infrastructure level — not as application-layer afterthoughts

---

## 2. API Modernization Layer

The connector framework in `platform_core/hcls_agent_platform/connectors/` acts as an **API abstraction and modernization layer** between agent tool calls and legacy vendor systems.

Each connector implements a minimal interface (`invoke(method, args) -> result`) and is registered in the gateway's `TOOL_REGISTRY`. The connector handles authentication, payload transformation, error normalization, and rate limiting for its target system. In demo mode, connectors return deterministic fixtures from `data/fixtures/` — the agent graph, gateway logic, and governance checks all execute normally; only the network call is bypassed.

This architecture delivers several platform capabilities:

- **Vendor API versioning insulation**: When Veeva updates its API, the connector absorbs the change without touching agent logic or gateway policy
- **Testability at every layer**: Agents, gateway policy, and governance checks can all run in CI without live vendor credentials
- **Connector reuse across agents**: The `safety` connector is shared by the PV agent and, for read-only case retrieval, by the Clinical Trial Ops agent — the gateway policy enforces which operations each agent is permitted
- **Progressive integration**: A customer can start with fixture connectors and activate live connectors one system at a time as integration testing is completed. The `safety` connector already ships a working **live HTTP implementation** (`LiveSafetyConnector`) demonstrated end-to-end against a reference service — flip `CONNECTOR_MODE=live` + `SAFETY_BASE_URL` to point at Argus/Veeva (see `02-pharmacovigilance-agent/demo/`)

---

## 3. MCP Authorization Gateway — Bedrock AgentCore Gateway + Identity

The gateway is the single enforcement point for every agent-to-system-of-record call. Its reference logic lives in `platform_core/hcls_agent_platform/mcp_gateway/`; in production it is expressed as **Amazon Bedrock AgentCore Gateway + AgentCore Identity**.

### Enforcement Order

Every tool call is fail-closed at each step:

```
1. Authenticate (IdP token verification, sub required)
         ↓
2. Authorize (deny-by-default, least-privilege intersection)
   permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]
         ↓
3. Human approval gate (required for all high_risk=True tools)
   Reviewer identity + timestamp bound into record (Part 11 e-signature linkage)
         ↓
4. Short-lived scoped token (AgentCore Identity / STS — no standing service accounts)
         ↓
5. Connector invocation
         ↓
6. PHI-masked append-only audit (DynamoDB / QLDB)
         ↓
7. Fail closed on any error
```

### Agent Tool Grants (Job Description as Code)

Each agent has a precisely scoped set of tools it may request:

| Agent | Read tools | Write/high-risk tools |
|---|---|---|
| 01 Regulatory Writing | `rim.get_obligations`, `rim.search_guidance`, `dms.get_document` | `rim.create_submission_draft`, `dms.put_draft` |
| 02 Pharmacovigilance | `safety.get_case`, `safety.search_duplicates`, `meddra.code_term`, `whodrug.code_drug` | `safety.write_case_draft`, `safety.submit_report` |
| 03 Clinical Trial Ops | `ctms.get_study_status`, `etmf.get_completeness`, `edc.get_subject_data` | `edc.create_query` |
| 04 Site & Patient Matching | `rwd.run_cohort_query`, `ctms.get_study_status` | — |
| 05 Quality / CAPA | `qms.get_complaint`, `qms.search_similar` | `qms.create_capa_draft`, `qms.close_capa` |
| 06 Protocol Design | `rim.search_guidance`, `rwd.run_cohort_query`, `ctms.get_study_status` | — |
| 07 RWE / HEOR | `rwd.run_cohort_query` | — |
| 08 Medical Affairs / MSL | `crm.get_hcp`, `dms.get_document` | `mlr.submit_for_review` |

A PV agent cannot reach the RIM. A Medical Affairs agent cannot write safety cases. These boundaries are enforced at the gateway, not by convention.

### Least-Privilege Intersection

The authorization model is an intersection, not a union:

- If the PV agent is granted `safety.submit_report` but the acting user is a `PV_PROCESSOR` (not a `PV_MEDICAL_REVIEWER`), the call is denied
- If the user is a `REGULATORY_APPROVER` but is interacting with the Medical Affairs agent (not the Regulatory Writing agent), the agent grant is absent and the call is denied
- Neither the agent's broad grant list nor the user's broad role set alone is sufficient — both must be in scope simultaneously

This ensures that compromised agent credentials cannot escalate beyond what any real user would be authorized to do.

### Mapping to AgentCore Gateway + Identity

| Platform concept | This codebase | Amazon Bedrock AgentCore |
|---|---|---|
| Tool registry | `policy.TOOL_REGISTRY` | Gateway **targets** |
| Authorization decision | `policy.decide()` intersection | Gateway authorizer + Identity scopes |
| Short-lived credential | `tokens.mint_scoped_token()` | AgentCore Identity credentials |
| Audit record | `audit.GatewayAuditLog` | CloudTrail + DynamoDB audit store |
| Backend adapters | `connectors/*` | Gateway target backends (Lambda/OpenAPI) |

The CloudFormation template `infra/cloudformation/agentcore-gateway.yaml` registers each tool as an AgentCore Gateway target and wires it to the Identity scope model.

---

## 4. Federated Identity and Agent Catalog Governance

### Federated Identity

The platform integrates with the customer's enterprise IdP (Okta, Microsoft Entra, Ping Identity, or any SAML 2.0 / OIDC provider) via Amazon Cognito as the federation layer. The `IdpMetadataUrl` CloudFormation parameter registers the customer IdP; Cognito maps IdP group claims to `custom:hcls_role` attributes that drive the gateway's `ROLE_ENTITLEMENTS` table.

This means:
- Role assignments live in the customer's HR-connected IdP, not in a standalone authorization database
- Joiners/movers/leavers propagate automatically as IdP group membership changes
- The regulated concept of "access control tied to job function" is enforced technically, not procedurally

### Agent Catalog Governance

Each agent in the suite is registered with a canonical identifier (`01-regulatory-writing`, `02-pharmacovigilance`, etc.) that is used as the primary key in the gateway's `AGENT_TOOL_GRANTS` table. Deploying a new agent requires:

1. Registering it in `AGENT_TOOL_GRANTS` with a minimal, justified tool set
2. Peer review of the tool grant list (the agent's "job description")
3. Registering any new tools in `TOOL_REGISTRY` with their connector kind, method, and risk classification
4. Updating the CloudFormation gateway template

This pull-request-based catalog governance ensures that agent capability creep is visible, reviewed, and version-controlled.

---

## 5. Agent-to-Agent (A2A) and Audit Standards

In multi-agent workflows — for example, a supervisor agent routing to a specialist PV or Regulatory agent — the A2A call passes the original user's identity claims, not the supervisor agent's identity. The downstream specialist agent's gateway sees the human's roles, not elevated supervisor permissions.

Audit records include:
- `session_id` (links all calls in a workflow)
- `agent_id` (which specialist handled the call)
- `tool` (which system-of-record operation was attempted)
- `decision` (ALLOW / DENY / PENDING_APPROVAL / ERROR)
- `user_sub` (IdP subject identifier — PHI-masked)
- `reviewer_sub` (bound at HITL gate)
- `timestamp_utc`
- `lineage` (source documents and case state used in the decision)

Audit records are written to an append-only DynamoDB table (no UpdateItem or DeleteItem allowed on the audit partition) with Point-in-Time Recovery enabled. For the highest-assurance use cases (e-signature linkage for Part 11 compliance), the same records are fanned to QLDB for cryptographically verified provenance.

---

## 6. Compliance Layer Mapping

The platform design maps to the overlapping regulatory frameworks as follows:

### HIPAA (45 CFR Parts 160/164)
- **PHI masking**: NER-based entity recognition replaces identifiers before any content enters an LLM prompt or audit record; the masking is stateless and deterministic
- **In-account inference**: Bedrock runs inside the customer's AWS account; PHI never traverses a network boundary to an external API
- **Minimum necessary**: The least-privilege intersection ensures agents access only the PHI fields their tool requires, not the full patient record
- **Audit controls**: Append-only audit satisfies the HIPAA Security Rule audit log requirement
- **BAA coverage**: AWS provides a Business Associate Agreement for Bedrock, DynamoDB, S3, KMS, and CloudWatch within the in-account deployment topology

### 21 CFR Part 11 (Electronic Records / Electronic Signatures)
- **Audit trail**: Every node in every agent graph appends a timestamped, attributable entry — actor, action, data sources, model version, outcome — to the append-only audit store
- **Electronic signature linkage**: At every HITL gate, the reviewer's IdP sub, roles, signature meaning ("I have reviewed and approve this content"), and timestamp are cryptographically bound to the approval record
- **System access controls**: RBAC enforced at the gateway; access is role-scoped and IdP-driven
- **Record integrity**: S3 Object Lock (WORM) for submitted documents; DynamoDB append-only for audit; QLDB for highest-assurance chains
- **Software validation**: The platform provides the control design; customer performs CSV/CSA per their SOP

### GxP — GCP / GLP / GMP (ALCOA+ data integrity)
- **Attributable**: Every record is attributed to a named user (IdP sub) and a named agent version
- **Legible**: Audit records are structured JSON in human-readable fields
- **Contemporaneous**: Records are written at the time of the action, not reconstructed
- **Original**: Source documents and grounding corpus are preserved with the audit record
- **Accurate**: Grounding verification enforces that every claim in a regulated draft is traceable to the source corpus; hallucinated content fails the grounding check before human review
- **Complete / Consistent / Enduring / Available**: Append-only DynamoDB with PITR + S3 Object Lock + KMS encryption at rest

### GVP / ICH E2B(R3) (Pharmacovigilance)
- The PV agent enforces CIOMS/E2B(R3) structural completeness as part of the grounding and eval harness before a case reaches the Medical Reviewer
- MedDRA coding is validated against the live MedDRA dictionary connector; coding confidence is surfaced to the reviewer
- Submission tool eligibility (`safety.submit_report`) is gated behind the `PV_MEDICAL_REVIEWER` role — the most junior role in the safety workflow cannot trigger an E2B submission

### FDA QMSR (21 CFR Part 820 — Quality Management System Regulation, effective February 2026)
- Agent 05 (Quality / CAPA) is designed against the QMSR framework: complaint intake, investigation support, CAPA draft generation, and CAPA closure
- Root-cause similarity search surfaces precedent CAPAs to support consistent classification — an explicit QMSR effectiveness expectation
- The `qms.close_capa` tool (irreversible) is restricted to the `QUALIFIED_PERSON` role in the gateway policy

### EU AI Act (Phased Implementation)
- Clinical and regulatory AI tools used in the EU are likely to be classified as **high-risk** under Annex III (medical devices and safety components) or under the general-purpose AI provisions
- The platform's control design anticipates EU AI Act requirements: defined context of use per agent, human oversight mandatory (enforced technically, not procedurally), accuracy/robustness/cybersecurity requirements addressed at the infrastructure level, transparency to deployers and users, logging for post-market monitoring
- The customer (as deployer under Article 16) is responsible for conducting the conformity assessment; this accelerator provides the technical documentation input

### GDPR (EU 2016/679) and Equivalent Data-Protection Laws
- Lawful basis for processing: the customer determines the lawful basis; the platform does not process personal data beyond what the customer's integration passes to it
- Data minimization: PHI masking and the minimum-necessary principle in the gateway reduce personal-data exposure in agent workflows
- Data residency: in-account Bedrock deployment ensures data does not leave the customer's designated AWS region
- Right to erasure: personal data in audit trails is pseudonymized (PHI-masked); the mapping table for pseudonymization is held by the customer under their GDPR-controlled key

### FDA/EMA Good Machine Learning Practices (January 2026)
- Context of use is defined per agent in the documentation and enforced in the tool grant policy
- Human accountability is technical, not merely procedural: the HITL gate is framework-enforced via LangGraph `interrupt_before`; the gateway will not execute a write tool without a verified human approval record
- Credibility controls are proportional to risk: read tools have no approval gate; low-risk draft generation has the grounding check; high-risk writes have the full HITL + reviewer identity binding
- Performance monitoring: the eval harness in `governance/evals/` provides the ongoing monitoring mechanism; prompt change control via the version registry provides the change-management mechanism

### SR 11-7 — Model Risk Management (Fed Guidance, Referenced in Life Sciences by FDA and IRB Analogues)
- The prompt is treated as part of the model: it is registered, hash-pinned, version-controlled, and subject to the same change-control process as code
- Initial validation: the eval harness over reviewed golden artifacts is the initial validation evidence
- Ongoing monitoring: the same harness runs in CI; performance drift triggers a review workflow
- Challenge and back-test: the red-team suite (`governance/redteam/`) provides adversarial challenge evidence

---

## 7. The Platform Roadmap

The platform is an accelerator, not a finished product. The roadmap below reflects the engagement arc for an SI deploying the suite at scale.

| Milestone | Platform capability | Engagement activity |
|---|---|---|
| **Assessment** | Architecture review; gap analysis against customer's compliance posture | 4–6 week assessment offering |
| **POC** | `EXTRACT_MODE=demo`; fixture connectors; one agent | 8–12 week POC; no AWS account required for initial demo |
| **Pilot** | Live Bedrock; one live connector (e.g., Veeva Vault RIM); IdP integration; one agent in production for one study or product | 12–16 week pilot; customer CSA scope begins |
| **Production (Agent 1)** | CSV complete; penetration test; full audit trail; validated connector | Post-pilot; engagement milestone |
| **Platform rollout** | Additional agents on the same platform infrastructure; shared gateway, audit, and identity stack | 6–12 months; cost of each additional agent decreases because platform is already in place |
| **Managed service** | SI operates the platform; customer uses the agents via a governed interface | Ongoing managed service; see `offerings/MANAGED-SERVICE-OFFERING.md` |
