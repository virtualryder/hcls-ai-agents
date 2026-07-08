# Integration Guide — Medical Affairs MSL Agent

The agent reaches CRM, DMS, and MLR systems through the MCP authorization
gateway, never a vendor SDK directly. Integration = implementing connectors +
mapping IdP roles + configuring the gateway policy.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-MA-MSL | `MSL` | `crm.get_hcp`, `dms.get_document` (read only) |
| GRP-MA-APPROVERS | `MEDICAL_AFFAIRS_APPROVER` | + `mlr.submit_for_review` (HIGH-RISK write) |

The `MEDICAL_AFFAIRS_APPROVER` role is the mandatory approver for the
`human_review_gate` node and the only role that can authorize
`mlr.submit_for_review`. Off-label or promotional findings always escalate to
this role — they are never auto-resolved.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | — | Parse HCP ID, meeting topic, therapy area, user claims |
| `pull_hcp_and_content` | `hcp_profiler`, `content_retriever`, `gateway_tools` → `crm.get_hcp`, `dms.get_document` | Pulls HCP profile from CRM; retrieves approved documents from DMS |
| `enrich_and_validate` | `hcp_profiler`, `next_best_action` | Enriches profile with interaction history; validates document currency; generates NBA |
| `draft_brief` | `brief_drafter` | LLM-authored pre-call brief grounded exclusively in on-label approved content |
| `compliance_check` | `compliance_checker` | Off-label, promotional, and grounding checks — deterministic, runs before HCP delivery |
| `human_review_gate` | — | Framework interrupt; `MEDICAL_AFFAIRS_APPROVER` reviews and approves or escalates |
| `finalize` | `gateway_tools` → `mlr.submit_for_review` (HIGH-RISK) | Submits approved brief to MLR system with approval token |

Full DAG: `intake → pull_hcp_and_content → enrich_and_validate → draft_brief → compliance_check → human_review_gate → finalize`

The `compliance_check` node may loop back to `draft_brief` for bounded
grounding-only revision. Off-label or promotional findings always route to
`human_review_gate` (ESCALATE path, not REVISE).

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `crm` | `crm.get_hcp` | Veeva CRM, Salesforce Health Cloud | READ |
| `dms` | `dms.get_document` | Veeva Vault, OpenText | READ |
| `mlr` | `mlr.submit_for_review` | Veeva Vault PromoMats, Zinc | **HIGH-RISK WRITE** — requires `MEDICAL_AFFAIRS_APPROVER` approv


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
- **AWS-native rebuild for this agent:** `../../aws-native-reference/08-medical-affairs-msl/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
