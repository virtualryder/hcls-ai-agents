# Suite Status & Changelog

Authoritative snapshot of what exists in this repository today. The README,
ENTERPRISE-PLATFORM, SOLUTION-FIELD-GUIDE, and per-agent docs reflect this state.

## Current state

| Dimension | Status |
|---|---|
| Agents | **8**, all built to flagship depth |
| AWS-native rebuilds | **8** (Strands + Step Functions, `waitForTaskToken` HITL) |
| Automated tests passing | **452** (platform 21 · governance 13 · agents 263 · native 155) |
| LLM | Anthropic Claude / in-account Amazon Bedrock + Guardrails / deterministic demo |
| MCP layer | Bedrock AgentCore Gateway + Identity (reference logic in `platform_core`) |
| IaC | CloudFormation quick-deploy (primary) + Terraform parity |
| Live reference path | Agent 02 — real Bedrock + real HTTP connector, end-to-end |
| GTM collateral | Executive deck, 5-slide teaser, one-page leave-behind |
| Maturity | Demonstrated + Deployable-by-design (production-readiness = engagement) |

## What "flagship depth" means (every agent)

- Full LangGraph workflow (`agent/` graph, state, nodes, prompts, persistence) with a
  framework-enforced human gate (`interrupt_before`) and a per-node audit trail.
- 5–8 tool modules incl. gateway-backed tools, a demo-fallback drafter, and a
  grounding/compliance checker.
- Deterministic fixtures (3 realistic records), a flagship-level test suite, and a
  multi-tab Streamlit dashboard.
- A four-document doc set: regulatory-compliance, integration-guide,
  aws-deployment-guide, roi-analysis.
- A matching AWS-native rebuild under `aws-native-reference/<agent>/`.

## Changelog (most recent first)

- **Executive deck PDF** — `HCLS-Agentic-AI-Suite-Executive-Overview.pdf` (leave-behind export of the 16-slide deck).
- **Per-agent deployment handbook PDFs** — `deliverables/agent-handbooks/HCLS-Deployment-Handbook-<agent>.pdf` for all 8 agents: each tailored with its own AgentId, systems, approver-role approval gate, native workflow, and agent-specific console mockups (Cognito/CloudFormation/Secrets/Step Functions/DynamoDB) under `docs/assets/console/<agent>/`.
- **Deployment Handbook PDF** — `HCLS-Deployment-Handbook.pdf`: branded, print-ready leave-behind (cover + all 7 figures, 20 pages) rendered from the handbook.
- **Console mockups** — 7 labeled, illustrative AWS Console screens (Figures 1–7) embedded in the Deployment Handbook and stored in `docs/assets/console/` (PNG + SVG source).
- **Deployment Handbook** — `docs/DEPLOYMENT-HANDBOOK.md`: console-level (click-by-click) + CLI deployment book, empty AWS account to a running governed agent, with a per-agent appendix. Linked from the README and every per-agent AWS deployment guide.
- **Onboarding** — `CONTRIBUTING.md` (new-engineer quickstart, conventions, recipes); per-agent integration/ROI docs refreshed to match the deepened code.
- **Field collateral** — added executive deck (`HCLS-Agentic-AI-Suite-Executive-Overview.pptx`),
  5-slide customer teaser (`HCLS-Customer-Teaser-5slide.pptx`), and one-page leave-behind
  (`HCLS-One-Pager.pdf` + `.pptx` source). Docs refreshed to reference them.
- **Live Bedrock + real-connector path (Agent 02)** — `LiveSafetyConnector` (real HTTP,
  `platform_core/.../connectors/live.py`), a local reference safety service, `demo/demo_live.py`,
  `demo/DEMO-LIVE.md`, and live-connector tests. `CONNECTOR_MODE=live` + `SAFETY_BASE_URL`
  swaps the local service for Argus/Veeva; `LLM_PROVIDER=bedrock` enables in-account inference.
- **Agents 03–08 deepened to flagship depth** — richer tools/nodes/apps/fixtures, flagship
  test suites, full 4-doc sets, and an AWS-native rebuild each.
- **AWS-native rebuild for Agent 02** added (registry now complete for all 8).
- **Flagship Agents 01 & 02**, shared `platform_core`, governance + eval framework, MCP
  authorization gateway (AgentCore Gateway + Identity reference), CloudFormation quick-deploy
  + Terraform parity, GTM/offerings/runbooks, and top-level docs.

## Verify

```bash
# platform + governance + evals
PYTHONPATH=platform_core pytest platform_core/tests governance -q
python -m governance.evals.run_evals
# any agent (demo mode, no API key)
cd 02-pharmacovigilance-agent && EXTRACT_MODE=demo pytest tests/ -q
# live PV path (local reference service; falls back to deterministic LLM)
PYTHONPATH=.:../platform_core python demo/demo_live.py
```
