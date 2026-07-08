# Integration Guide — Protocol Design Agent

The agent reaches every system of record through the MCP authorization gateway,
never a vendor SDK directly. Integration = implementing connectors + mapping IdP
roles + configuring the gateway policy.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-CLINICAL-SCIENTISTS | `CLINICAL_SCIENTIST` | draft, read RIM / RWD / CTMS |
| GRP-MEDICAL-REVIEWERS | `MEDICAL_REVIEWER` | + approve protocol sections |

No gateway tool in this agent is currently tagged HIGH-RISK for read operations,
but the `human_review_gate` node is framework-enforced (`interrupt_before`) so no
protocol section is finalized without a `MEDICAL_REVIEWER` sign-off.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | — | Parse indication, phase, design parameters, user claims |
| `search_guidance` | `guidance_searcher`, `gateway_tools` → `rim.search_guidance` | Retrieves regulatory guidance documents from RIM |
| `feasibility_estimate` | `feasibility_estimator`, `gateway_tools` → `rwd.run_cohort_query`, `ctms.get_study_status` | RWD cohort size and CTMS historical precedent |
| `draft_protocol_sections` | `protocol_drafter` | LLM drafts endpoints, eligibility, schedule grounded in guidance + feasibility |
| `risk_assessment` | `risk_assessor` | Protocol risk scoring (amendment risk, feasibility risk, regulatory risk) |
| `quality_check` | `protocol_checker` | Regulatory completeness + grounding; routes to revise or approve |
| `human_review_gate` | — | Framework interrupt; `CLINICAL_SCIENTIST` or `MEDICAL_REVIEWER` reviews and approves |
| `finalize` | — | Locks the approved protocol package and audit trail |

Full DAG: `intake → search_guidance → feasibility_estimate → draft_protocol_sections → risk_assessment → quality_check → human_review_gate → finalize`

The `quality_check` node may loop back to `draft_protocol_sections` for bounded
revision before forwarding to `human_review_gate`.

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `rim` | `rim.search_guidance` | Veeva Vault RIM / Documentum / internal guidance library | READ |
| `rwd` | `rwd.run_cohort_query` | Optum CDM, Flatiron, TriNetX, internal EHR warehouse | READ — aggregate counts only |
| `ctms` | `ctms.get_study_status` | Veeva Vault CTMS / Medidata / Oracle Siebel CTMS | READ |

All three are read-only for this agent. No HIGH-RISK writes are registered.

Switch with `CONNECTOR_MODE=live`.

## 4. Live connector pattern

The worked reference for going live is `LiveSafetyConnector` in
`platform_core/hcls_agent_p


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
- **AWS-native rebuild for this agent:** `../../aws-native-reference/06-protocol-design/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
