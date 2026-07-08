# Integration Guide — Clinical Trial Ops Agent

The agent reaches every system of record (CTMS, eTMF, EDC) through the MCP
authorization gateway, never a vendor SDK directly. Integration = implementing
connectors + mapping IdP roles + configuring gateway policy.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-CLINOPS-CRA | `CRA` | read CTMS / eTMF / EDC |
| GRP-CLINOPS-LEAD | `CLINOPS_LEAD` | + approve EDC query creation (HIGH-RISK write) |
| GRP-CLINOPS-CTM | `CTM` | + read audit trail; escalation recipient |

The `CLINOPS_LEAD` role is the mandatory approver for the `human_review_gate`
node and the only role that can authorize `edc.create_query`.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | — | Parse study ID, user claims, review scope |
| `pull_study_data` | `gateway_tools` → `ctms.get_study_status`, `etmf.get_completeness`, `edc.get_subject_data` | Reads study status, TMF gaps, and EDC subject data |
| `analyze_tmf` | `tmf_analyzer` | ICH E6(R2) zone gap analysis |
| `detect_issues` | `risk_scorer` | Enrollment, query backlog, visit compliance issues |
| `draft_queries` | `query_drafter` | EDC query drafts (status DRAFT; not yet written to EDC) |
| `draft_briefing` | `study_briefer` | LLM-authored study health briefing |
| `quality_check` | `quality_checker` | Grounding + completeness; routes to revise or approve |
| `human_review_gate` | — | Framework interrupt; `CLINOPS_LEAD` reviews and approves |
| `finalize` | `gateway_tools` → `edc.create_query` (HIGH-RISK) | Issues approved queries to EDC via gateway |

Full DAG: `intake → pull_study_data → analyze_tmf → detect_issues → draft_queries → draft_briefing → quality_check → human_review_gate → finalize`

The `quality_check` node may loop back to `draft_briefing` for bounded revision
before forwarding to `human_review_gate`.

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `ctms` | `ctms.ge


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
  `../../infra/cloudformation/README.md`; Terraform reference skeleton (see docs/TERRAFORM-AND-GOVCLOUD-STATUS.md) in `../../infra/terraform/`.
- **AWS-native rebuild for this agent:** `../../aws-native-reference/03-clinical-trial-ops/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
