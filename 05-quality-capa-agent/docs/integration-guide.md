# Integration Guide — Quality CAPA Agent

The agent reaches every system of record through the MCP authorization gateway,
never a vendor SDK directly. Integration = implementing connectors + mapping IdP
roles + configuring the gateway policy.

## 1. Identity (IdP to roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-QA-SPECIALISTS | `QA_SPECIALIST` | classify events, read QMS complaint and similar-event data |
| GRP-QP | `QUALIFIED_PERSON` | + create CAPA draft (HIGH-RISK write), close CAPA (HIGH-RISK irreversible write) |

Both `qms.create_capa_draft` and `qms.close_capa` are tagged HIGH-RISK in the
gateway policy and require a `QUALIFIED_PERSON` approval payload to be allowed.

## 2. Workflow nodes and tools

| Node | Tool(s) invoked | Notes |
|---|---|---|
| `intake` | — | Parse complaint/deviation record, user claims, event context |
| `classify_event` | `complaint_classifier`, `gateway_tools` → `qms.get_complaint` | Retrieves event record; classifies type, severity, regulatory flag |
| `search_similar_events` | `similarity_search`, `gateway_tools` → `qms.search_similar` | Semantic similarity search across closed CAPA history |
| `root_cause_analysis` | `root_cause_analyzer` | Ishikawa / 5-Why heuristics from event corpus |
| `draft_capa` | `capa_drafter` | LLM-authored CAPA plan grounded in root cause hypotheses |
| `quality_check` | `quality_checker` | GMP grounding + completeness; routes to revise or approve |
| `human_review_gate` | — | Framework interrupt; `QUALIFIED_PERSON` reviews and approves |
| `finalize` | `gateway_tools` → `qms.create_capa_draft` (HIGH-RISK) | Creates CAPA record in QMS with approval token |

Full DAG: `intake → classify_event → search_similar_events → root_cause_analysis → draft_capa → quality_check → human_review_gate → finalize`

The `quality_check` node may loop back to `draft_capa` for bounded revision
before forwarding to `human_review_gate`.

`qms.close_capa` is registered as a HIGH-RISK tool for the closure workflow
(invoked separately after CAPA execution is complete and verified).

## 3. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Gateway tool | System | Risk |
|---|---|---|---|
| `qms` | `qms.get_complaint` | Veeva Vault QMS / TrackWise / MasterControl | READ |
| `qms` | `qms.search_similar` | Veeva Vault QMS / TrackWise / MasterControl | READ |
| `qms` | `qms.create_capa_draft` | Veeva Vault QMS / TrackWise / MasterControl | **HIGH-RISK WRITE** — requires `QUALIFIED_PERSON` approval |
| `qms` | `qms.close_cap


<!-- live-aws-xref -->
## Going live (Bedrock + real connectors)

This agent runs offline in `EXTRACT_MODE=demo`. To go live, keep the same gateway
path and swap connector/LLM by configuration — no agent code changes:

- **Real connectors:** implement the typed methods in
  `platform_core/hcls_agent_platform/connectors/live.py`, mirroring the worked
  reference `LiveSafetyConnector` (real HTTP, stdlib-only, credentials via
  `get_secret`). Preserve the fixture method signatures. Activate with
  `CONNECTOR_MODE=live` and the system's `*_BASE_URL`.
- **In-account inference:** set `LLM_PROVIDER=bedrock` + `BEDROCK_GUARDRAIL_ID`.
- **End-to-end worked example:** `02-pharmacovigilance-agent/demo/demo_live.py`
  and `02-pharmacovigilance-agent/demo/DEMO-LIVE.md` show the full live path
  (live Bedrock + a real HTTP connector against a reference service).

## AWS deployment

- **Quick deploy:** `../../infra/cloudformation/` (nested-stack quickstart) — see
  `../../infra/cloudformation/README.md`; Terraform parity in `../../infra/terraform/`.
- **AWS-native rebuild for this agent:** `../../aws-native-reference/05-quality-capa/`
  (Strands + Step Functions with a `waitForTaskToken` human gate), plus the
  container-lift path on AgentCore Runtime via `../../aws-native-reference/_shared/runtime`.
