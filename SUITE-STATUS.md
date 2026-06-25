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
| MCP layer | Two interchangeable gateway modes — portable (API Gateway + Cognito JWT) and managed (Bedrock AgentCore Gateway + Identity) — both fronting shared connector Lambdas (reference logic in `platform_core`) |
| IaC | One-command CloudFormation quick-deploy: connectors + dual gateway + native/container agent, deployable in a new account in any Region (`scripts/build_lambdas.sh` + `scripts/deploy.sh`) + Terraform parity |
| Live reference path | Agent 02 — real Bedrock + real HTTP connector, end-to-end |
| GTM collateral | **Cited, generated AWS-style deck system: 8 per-agent decks + executive overview + CIO/CISO board deck** (`decks/`, `make decks`), each with PDF leave-behind (`make decks-pdf`); GTM citation spine (`gtm/HCLS-DECK-SOURCES.md`, `DECK-CONTENT-SPEC.md`, `DEMO-STORYBOARD.md`) + SA-fillable ROI calculator (`gtm/roi-calculator/`, `make roi`); plus the original executive deck, 5-slide teaser, and one-page leave-behind |
| Enablement | `docs/SA-SE-ENABLEMENT-GUIDE.md`, `docs/FAQ.md`, `docs/CREATE-A-NEW-AGENT.md`; CI in `.github/workflows/ci.yml` (tests · compile · deck build · cfn-lint) |
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

- **Cited AWS-style GTM deck system + GTM citation spine** — brought GTM collateral to (and past) the EDU/SLG standard:
  - **`decks/` — 11 generated decks.** `build-agent-decks.js` (pptxgenjs) drives 8 per-agent AWS-style decks (issue → cost of doing nothing → governed pipeline → AWS architecture & traffic flow → proof/deploy) + the executive overview from one `AGENTS` content array; `build-cio-deck.js` drives the **CIO / CISO / Director-of-Architecture adoption-review** board deck (verdict, six gateway controls, shortfalls, 3-part shared-responsibility matrix, phased path, go/no-go). AWS palette + speaker notes on every slide. `make decks` builds + recompresses; `make decks-pdf` exports print-ready PDF leave-behinds.
  - **`gtm/` — citation spine.** `HCLS-DECK-SOURCES.md` (every deck stat tagged by source class — `[gov/peer-reviewed]`/`[industry-research]`/`[sector-press/estimate]`/`[vendor]`/`[modeled]` — with URLs; vendor/modeled figures flagged, never lead), `DECK-CONTENT-SPEC.md` (per-agent content contract), `DEMO-STORYBOARD.md` (repeatable ~25-min customer demo), and `roi-calculator/` (SA-fillable XLSX + generator, `make roi`).
  - **Enablement + CI.** README upgraded with the new collateral, a CI badge, and explicit CIO/CSO/Architect positioning; new `docs/SA-SE-ENABLEMENT-GUIDE.md`, `docs/FAQ.md`, `docs/CREATE-A-NEW-AGENT.md`; new `.github/workflows/ci.yml` (platform/governance/agent tests · byte-compile · deck build · cfn-lint).
- **Deployable-in-a-new-account hardening** — closed the gaps that blocked a clean first deploy and made both deployment paths real:
  - **Connector Lambdas** (`infra/cloudformation/connectors.yaml` + `aws-native-reference/_shared/connector/handler.py`) — one governed backend per system of record; every gateway target now resolves to a real function that runs each call through `platform_core`'s `MCPGateway` (deny-by-default, approval gate, audit). Validated with a 5-case enforcement smoke test (ALLOW / PENDING_APPROVAL / wrong-kind DENY / API-Gateway-proxy / AgentCore-input shapes).
  - **Two MCP gateway modes, one policy** — new `gateway-portable.yaml` (API Gateway HTTP API + Cognito JWT authorizer, **any Region**) alongside the fixed `agentcore-gateway.yaml` (now references real connector ARNs, all 12 targets). Pick with `GatewayMode`.
  - **IAM fix** — the shared agent role now grants DynamoDB (audit/review), S3 (WORM), Step Functions task callbacks, CloudWatch Logs, and connector invoke (previously missing → HITL-notify/finalize would fail at runtime).
  - **Real container mode** — `agent-service.yaml` now provisions an ECS Fargate service (ARM64) instead of a placeholder comment; the running service *is* the agent.
  - **Build + deploy automation** — `scripts/build_lambdas.sh` vendors Strands + `platform_core` into each zip (fixes cold-start `ImportError`); `scripts/deploy.sh` stages to S3 and deploys the master stack for a new account in one command (`make build-lambdas` / `make deploy`).
  - **New guide** — `docs/DEPLOY-QUICKSTART.md` (empty account → live agent, including "creating the agent itself"); README, `DEPLOYMENT-HANDBOOK.md`, infra READMEs, `DEPLOY-ALL.md`, and all 8 per-agent `DEPLOY.md` updated to match.
- **AWS GTM mechanics pack** — five new `docs/` files covering the questions AWS sellers and SAs ask before a deal can progress: `AWS-FUNDING-AND-GTM.md` (MAP/PoA/ISV Accelerate), `WELL-ARCHITECTED-REVIEW.md` (WAF + GenAI Lens pillar mapping), `SHARED-RESPONSIBILITY-MATRIX.md` (AWS vs. SI vs. institution), `AWS-ACCOUNT-PREREQUISITES.md` (pre-flight checklist), `AWS-MARKETPLACE-PATH.md` (private offer mechanics).
- **Sales artifacts** — `offerings/BATTLECARD.md` (qualifying questions, discovery cheat-sheet, objection + competitor one-liners), `offerings/SOW-TEMPLATE.md` (fill-in-the-blank POC/Pilot SOW shell), `offerings/TCO-MODEL.md` (Bedrock inference + infrastructure cost estimates + per-agent ROI worksheet with SA number-entry guide).
- **A2A orchestration stance + reference** — `ENTERPRISE-PLATFORM.md` §5 expanded to **ADR-001** (in-process LangGraph today; A2A-through-AgentCore when multi-agent is needed), plus a runnable governed reference hop `platform_core/hcls_agent_platform/a2a/` (identity-propagating, least-privilege, audited; 5 tests).
- **`make handbooks` build tooling** — versioned generators in `tooling/handbooks/` + a repo-root `Makefile`; figures, the master PDF, and the 8 per-agent PDFs regenerate from source with dependency tracking (edit a profile -> only the affected PDFs rebuild).
- **MCP-layer account explainer** — `docs/WHY-THE-MCP-LAYER.md`: plain-English why-and-why-now for the governed access layer, with a talk track and objection handling.
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
