# Integration Guide — RWE/HEOR Evidence Agent

The agent reaches the real-world data platform through the MCP authorization
gateway, never a vendor SDK directly. Integration = implementing connectors +
mapping IdP roles + configuring the gateway policy.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-RWE-ANALYSTS | `HEOR_ANALYST` | run cohort queries, view results and synthesis |
| GRP-RWE-EPIDEMIOLOGISTS | `EPIDEMIOLOGIST` | + approve evidence synthesis for publication |

The `EPIDEMIOLOGIST` role is the mandatory approver for the `human_review_gate`
node. No synthesis is released without their sign-off.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | — | Parse research question, indication, comparators, user claims |
| `define_cohort` | `cohort_definer` | Translates research question to computable ICD-10 cohort specification |
| `run_cohort_query` | `cohort_query_runner`, `gateway_tools` → `rwd.run_cohort_query` | Executes cohort query; returns aggregate de-identified statistics |
| `assess_data_quality` | `data_quality_assessor` | Completeness, balance, confounding assessment before LLM is invoked |
| `synthesize_evidence` | `evidence_synthesizer` | LLM narrative synthesis from pre-computed statistics only |
| `grounding_check` | `rwe_checker` | Numbers traceable to stats corpus; no causal claims; routes to revise or approve |
| `human_review_gate` | — | Framework interrupt; `EPIDEMIOLOGIST` reviews and approves |
| `finalize` | — | Locks audit trail; marks synthesis as approved |

Full DAG: `intake → define_cohort → run_cohort_query → assess_data_quality → synthesize_evidence → grounding_check → human_review_gate → finalize`

The `grounding_check` node may loop back to `synthesize_evidence` for bounded
revision before forwarding to `human_review_gate`.

**Important**: the LLM is invoked only in `synthesize_evidence` and receives only
pre-computed statistics from `assess_data_quality`. It never generates new
statistical estimates.

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `rwd` | `rwd.run_cohort_query` | Optum CDM, TriNetX, Flatiron, IQVIA | READ — aggregate counts only; no PHI |

This is the only gateway tool registered for agent `07-rwe-heor`. No write tools
are registered.

Switch with `CONNECTOR_MODE=live`.

## 4. Live connect


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
- **AWS-native rebuild for this agent:** `../../aws-native-reference/07-rwe-heor/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
