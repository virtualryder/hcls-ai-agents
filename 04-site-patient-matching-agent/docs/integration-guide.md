# Integration Guide — Site and Patient Matching Agent

The agent reaches every system of record (RWD, CTMS) through the MCP
authorization gateway, never a vendor SDK directly. Integration = implementing
connectors + mapping IdP roles + configuring the gateway policy.

PHI never crosses the agent boundary — only aggregate, de-identified counts are
processed.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-CLINOPS-CRA | `CRA` | read RWD cohort results, view rankings |
| GRP-SITE-SELECTION | `SITE_SELECTION_LEAD` | + approve ranked site lists before outreach |
| GRP-CLINOPS-CTM | `CTM` | escalation reviewer for critical equity flags |

The `SITE_SELECTION_LEAD` role is the mandatory approver for the
`human_review_gate` node. No site outreach is initiated until they sign off.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | -- | Parse protocol, eligibility criteria, study ID, user claims |
| `translate_criteria` | `eligibility_translator` | Converts free-text criteria to CDISC-aligned computable logic |
| `run_cohort_query` | `gateway_tools` -> `rwd.run_cohort_query` | Returns aggregate de-identified site counts only |
| `estimate_cohorts` | `cohort_estimator` | Projects enrollment feasibility per site and portfolio |
| `rank_sites` | `site_ranker` | Scores and ranks sites by eligible pool, activation state |
| `fairness_review` | `fairness_checker` | Flags demographic under-representation vs. disease-prevalence benchmarks |
| `human_review_gate` | -- | Framework interrupt; `SITE_SELECTION_LEAD` reviews and approves |
| `finalize` | `gateway_tools` -> `ctms.get_study_status` | Annotates the final ranked list with current CTMS state |

Full DAG: `intake -> translate_criteria -> run_cohort_query -> estimate_cohorts -> rank_sites -> fairness_review -> human_review_gate -> finalize`

The `fairness_review` node may loop back to `rank_sites` for bounded revision
before forwarding to `human_review_gate`.

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `rwd` | `rwd.run_cohort_query` | Optum CDM, TriNetX, Flatiron, IQVIA | READ -- aggregate counts only; no PHI |
| `ctms` | `ctms.get_study_status` | Veeva CTMS / Medidata Rave | READ |

No HIGH-RISK writes are registered for this agent. The human approver triggers
site outreach through the site activation workflow after approving the ranked list.

Switch with `CONNECTOR_MODE=live`.

## 4. Live connector pattern

The worked reference for going live is `LiveSafetyConnector` in
`platform_core/hcls_agent_platform/connectors/live.py` and the runbook at
`02-pharmacovigilance-agent/demo/DEMO-LIVE.md`. Apply the same pattern to each
`kind` above:

- Set `CONNECTOR_MODE=live`.
- Resolve bearer tokens via `get_secret` (Secrets Manager with env-var fallback).
- Implement against the vendor REST contract; preserve the fixture method signatures
  so no agent code changes are required.
- The RWD connector must enforce cell suppression (counts < 11 suppressed) per
  45 CFR 164.514(b) Safe Harbor or 164.514(e) Expert Determination.

## 5. Gateway policy

`mcp_gateway/policy.py` grants agent `04-site-patient-matching` the
`rwd.run_cohort_query` and `ctms.get_study_status` tools (both read-only).
The gateway rejects any response containing row-level patient identifiers.
Tighten `ROLE_ENTITLEMENTS` to match your org. In production these become
AgentCore Gateway targets + Identity scopes
(see `../../infra/cloudformation/agentcore-gateway.yaml`).

## 6. RWD de-identification requirements

`rwd.run_cohort_query` must return ONLY aggregate, de-identified counts:

- Cell suppression for counts < 11 (HIPAA Safe Harbor k-anonymity threshold).
- No patient-level records returned at any stage.
- Queries logged in the audit trail per 21 CFR Part 11.
- Configure `HIPAA_SAFE_HARBOR` or `EXPERT_DETERMINATION` mode in your RWD platform.

## 7. LLM provider

Dev: `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`.
Production: `LLM_PROVIDER=bedrock` with a VPC endpoint and `BEDROCK_GUARDRAIL_ID`
set so no PHI or off-label conclusions are generated.

## 8. Persistence

Set `DATABASE_URL` for PostgresSaver (resumable HITL, durable audit trail).
Without it the demo uses in-memory checkpointing.

## 9. AWS cross-links

- AWS-native rebuild: `../../aws-native-reference/04-site-patient-matching/`
- Quick-deploy CloudFormation: `../../infra/cloudformation/`

## 10. Validation

Run `pytest tests/` and the governance evals. Key checks: de-identification
enforcement, `fairness_checker` flags trigger correctly, `SITE_SELECTION_LEAD`
HITL gate present in completed steps, and no row-level patient data in state.


<!-- live-aws-xref -->
## Going live (Bedrock + real connectors)

This agent runs offline in `EXTRACT_MODE=demo`. To go live, keep the same gateway
path and swap connector/LLM by configuration — no agent code changes:

- **Real connectors:** implement the typed methods in
  `platform_core/hcls_agent_platform/connectors/live.py`, mirroring the worked
  reference `LiveSafetyConnector` (real HTTP, stdlib-only, credentials via
  `get_secret`). Preserve the fixture method signatures. Activate with
  `CONNECTOR_MODE=live` and the system's `*_BASE_URL`.
- **Private-connectivity inference:** set `LLM_PROVIDER=bedrock` + `BEDROCK_GUARDRAIL_ID`.
- **End-to-end worked example:** `02-pharmacovigilance-agent/demo/demo_live.py`
  and `02-pharmacovigilance-agent/demo/DEMO-LIVE.md` show the full live path
  (live Bedrock + a real HTTP connector against a reference service).

## AWS deployment

- **Quick deploy:** `../../infra/cloudformation/` (nested-stack quickstart) — see
  `../../infra/cloudformation/README.md`; Terraform parity in `../../infra/terraform/`.
- **AWS-native rebuild for this agent:** `../../aws-native-reference/04-site-patient-matching/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
