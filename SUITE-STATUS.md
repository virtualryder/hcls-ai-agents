# Suite Status & Changelog

Authoritative snapshot of what exists in this repository today. The README,
ENTERPRISE-PLATFORM, SOLUTION-FIELD-GUIDE, and per-agent docs reflect this state.

## Current state

| Dimension | Status |
|---|---|
| Agents | **9**, all built to flagship depth (01–08 core lifecycle + 09 Manufacturing Batch-Review) |
| AWS-native rebuilds | **9** (Strands + Step Functions, `waitForTaskToken` HITL) |
| Automated tests passing | **519** (platform 50 · governance 7 · agents 277 · native 185), verified in one command via `make test`; **all 9 golden paths also deployed + run end-to-end in a clean AWS account** |
| LLM | Anthropic Claude / in-account Amazon Bedrock + Guardrails / deterministic demo |
| MCP layer | Portable gateway (API Gateway + Cognito JWT) is the **supported default**; a **managed Bedrock AgentCore Gateway** path is **experimental** (each target additionally requires a ToolSchema — `agentcore-gateway.yaml`). Both front shared connector Lambdas (reference logic in `platform_core`) |
| IaC | One-command CloudFormation quick-deploy: connectors + dual gateway + native/container agent, deployable in a new account in any Region (`scripts/build_lambdas.sh` + `scripts/deploy.sh`) + Terraform parity |
| Live reference path | Agent 02 — real Bedrock + real HTTP connector, end-to-end |
| GTM collateral | **Cited, generated AWS-style deck system: 8 per-agent decks + executive overview + CIO/CISO board deck** (`decks/`, `make decks`), each with PDF leave-behind (`make decks-pdf`); GTM citation spine (`gtm/HCLS-DECK-SOURCES.md`, `DECK-CONTENT-SPEC.md`, `DEMO-STORYBOARD.md`) + SA-fillable ROI calculator (`gtm/roi-calculator/`, `make roi`); plus the original executive deck, 5-slide teaser, and one-page leave-behind |
| Enablement | `docs/SA-SE-ENABLEMENT-GUIDE.md`, `docs/FAQ.md`, `docs/CREATE-A-NEW-AGENT.md`; CI in `.github/workflows/ci.yml` (tests · compile · deck build · cfn-lint) |
| Roadmap agents | **1** cited deck + design spec at Documented maturity — 10 Scientific Intelligence & Target Discovery (R&D); see `docs/specs/`. (09 was promoted to a built agent.) |
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

- **Live AWS deploy validation (all 9 golden paths)** — every per-agent SAM golden path was deployed into a clean account (us-east-1), ran the full governed workflow (Assemble→…→`waitForTaskToken` human gate→bound separation-of-duties approval→Finalize) to **SUCCEEDED**, and was torn down. Surfaced + fixed ~10 deploy/runtime issues invisible to cfn-lint (layer staging incl. `strands_agent`, Bedrock `PROMPT_ATTACK`=NONE, two ASL data contracts, identity lineage, the **human-authority commit** path for withheld consequential tools, SAM state-machine update-on-content-change, 07 `Synthesize`→`DraftFn`). New `docs/GOLDEN-PATH-DEPLOY-NOTES.md`; generic `infra/_smoke/resume_any.py`. Suite **519** green.

- **External-review remediation (P0)** — an independent review (58/100) found gaps between the control
  narrative and the *deployed* path; all P0 items closed and verified one-command (`docs/CHATGPT-REVIEW-REMEDIATION-PLAN.md`):
  deployed-path **bound-approval enforcement** in `finalize` (SoD/expiry/args/single-use, `STRICT_APPROVAL` fail-closed,
  governed-connector submit); **authorizer-only identity** in the connector; review/approval unified on `approval_id`;
  **immutable fail-closed audit** (conditional `PutItem`, no Update/BatchWrite IAM); **customer IdP federation** (Cognito
  SAML/OIDC provider + `docs/IDP-FEDERATION-RUNBOOK.md`); **VPC PrivateLink isolation** (gateway + interface endpoints,
  flow logs, 443-only egress, VPC-attached Lambdas) with the VPC claim corrected to accurate framing; **container path**
  completed (internal ALB + `/ping`), SAM golden path canonical; **CI fail-closed**. Suite **492 → 503**.

- **Security & deployability deepening (SLG-parity pass)** — closed the gaps where SLG-AI-Agents went deeper, so HCLS now exceeds it on every axis:
  - **CISO/CIO security answer kit:** `SECURITY.md` + `docs/THREAT-MODEL.md` (STRIDE→control→file) + `docs/NIST-800-53-CONTROL-MATRIX.md` + `docs/OWASP-LLM-ATLAS-MAPPING.md` + `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` + `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`, plus a README "CISO/CIO question index".
  - **Defense-in-depth in code:** the irreversible commit (`safety.submit_report`/`qms.close_capa`/`mes.record_disposition`) is **withheld from every agent grant** (`policy.CONSEQUENTIAL_COMMITS`), enforced by `test_consequential_actions_withheld_from_agents`; a bound human-approval primitive (`mcp_gateway/approvals.py`: single-use, separation-of-duties, args-bound; `STRICT_APPROVAL` for prod). 02/09 finalize now write reversible drafts.
  - **One-command test harness:** `make test` / `scripts/run_all_tests.sh` runs all **503** tests across 20 suites and prints one total; root `conftest.py` + `pytest.ini`.
  - **Deploy ergonomics:** `infra/cloudformation/edge.yaml` (CloudFront + WAF) closes the edge-in-IaC gap; **per-agent SAM golden paths** (`infra/golden-path-<agent>/` × 9: `template.yaml` + `deploy.sh` + `destroy.sh` + `smoke_test.sh` + `mint_approval.py` + layer) so an SA deploys one agent from a single folder — all cfn-lint clean. Index: `infra/GOLDEN-PATHS.md`.
  - **Hygiene:** `CHANGELOG.md`, `VERSION`, `SOURCES.md`; `decks/leave-behinds/HCLS-AI-Agent-Suite-COMBINED.pdf` (77-page all-in-one); `09-manufacturing-batch-review` added to the Lambda build list.

- **Agent 09 (Manufacturing Batch-Review) built to flagship depth** — promoted from roadmap to a built agent: `09-manufacturing-batch-review-agent/` (LangGraph review-by-exception workflow with a QA release gate, gateway-backed `mes`/`lims` tools, deterministic exception scanner, demo-fallback drafter + grounding check, 3 batch fixtures, Streamlit dashboard, 4-doc set) + an AWS-native rebuild (`aws-native-reference/09-manufacturing-batch-review/`: Strands + Step Functions `waitForTaskToken` QA gate). New connector kinds `mes` + `lims` (policy + fixtures + `connectors.yaml` targets) and roles `MFG_OPERATOR` / `QA_RELEASE`. **36 new tests pass** (14 agent + 22 native); platform/governance/agent-02 unaffected. Suite is now **9 built agents**; 10 (Scientific Intelligence) remains roadmap.

- **Cited AWS-style GTM deck system + GTM citation spine** — brought GTM collateral to (and past) the EDU/SLG standard:
  - **`decks/` — 12 generated decks (10 per-agent incl. 2 roadmap + executive overview + CIO board deck).** `build-agent-decks.js` (pptxgenjs) drives 8 per-agent AWS-style decks (issue → cost of doing nothing → governed pipeline → AWS architecture & traffic flow → proof/deploy) + the executive overview from one `AGENTS` content array; `build-cio-deck.js` drives the **CIO / CISO / Director-of-Architecture adoption-review** board deck (verdict, six gateway controls, shortfalls, 3-part shared-responsibility matrix, phased path, go/no-go). AWS palette + speaker notes on every slide. `make decks` builds + recompresses; `make decks-pdf` exports print-ready PDF leave-behinds.
  - **`gtm/` — citation spine.** `HCLS-DECK-SOURCES.md` (every deck stat tagged by source class — `[gov/peer-reviewed]`/`[industry-research]`/`[sector-press/estimate]`/`[vendor]`/`[modeled]` — with URLs; vendor/modeled figures flagged, never lead), `DECK-CONTENT-SPEC.md` (per-agent content contract), `DEMO-STORYBOARD.md` (repeatable ~25-min customer demo), and `roi-calculator/` (SA-fillable XLSX + generator, `make roi`).
  - **Roadmap/expansion agents 09 & 10.** Added cited per-agent decks (`decks/HCLS-09/10-*.pptx`) + DECK-SOURCES entries + design specs (`docs/specs/`) for Manufacturing Batch-Review (CMC/GxP) and Scientific Intelligence & Target Discovery (R&D), extending the lifecycle to manufacturing and discovery. Built via an `EXPANSION` array; the executive overview stays at the 8 built agents to keep maturity honest.
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
