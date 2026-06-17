# Contributing & Onboarding

Welcome. This repo is a **governed, AWS-native accelerator** of eight Life Sciences
AI agents plus the shared platform that makes them deployable in a regulated
environment. This guide gets a new SI engineer or solution architect productive
in about 30 minutes. Read `SUITE-STATUS.md` for the current state, `README.md`
for the full overview, and `ENTERPRISE-PLATFORM.md` for the architecture story.

## 1. Ten-minute quickstart (no API key, no AWS)

```bash
# Python 3.11+
cd 01-regulatory-writing-agent
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../platform_core

export EXTRACT_MODE=demo        # deterministic; no LLM call, no credentials
streamlit run app.py            # http://localhost:8501  — click through the workflow
EXTRACT_MODE=demo pytest tests/ -q
```

Run the platform + governance suites from the repo root:

```bash
PYTHONPATH=platform_core pytest platform_core/tests governance -q
python -m governance.evals.run_evals
```

Everything runs offline. `EXTRACT_MODE=demo` routes tool calls through fixture
connectors and bypasses the model, so the full graph (intake → … → human gate →
finalize) executes against deterministic data.

## 2. Repo map

| Path | What it is |
|---|---|
| `0N-*-agent/` | The eight agents (LangGraph workflow + tools + app + tests + docs) |
| `platform_core/hcls_agent_platform/` | Shared platform: LLM factory, PHI masking, **MCP gateway**, connectors, secrets, auth, tracing |
| `governance/` | Grounding, prompt registry, eval harness, HITL-gate tests, red team, fairness |
| `aws-native-reference/` | Per-agent AWS-native rebuild (Strands + Step Functions) + shared AgentCore runtime |
| `infra/cloudformation/` | Quick-deploy nested stacks (primary IaC) |
| `infra/terraform/` | Terraform parity |
| `docs/` | Suite architecture + stakeholder security briefings |
| `offerings/` , `runbooks/` | GTM packaging + operational runbooks |
| `*.pptx`, `HCLS-One-Pager.pdf` | Field-enablement collateral |

## 3. Anatomy of an agent (every agent is the same shape)

```
0N-name-agent/
├── agent/
│   ├── state.py        # TypedDict state + RecommendedAction enum
│   ├── prompts.py      # prompts, registered with the governance prompt registry
│   ├── nodes.py        # one function per workflow step; each appends an audit entry
│   ├── graph.py        # LangGraph DAG; compiles with interrupt_before=["human_review_gate"]
│   └── persistence.py  # MemorySaver (dev) / PostgresSaver (prod via DATABASE_URL)
├── tools/
│   ├── gateway_tools.py # the ONLY path to systems of record (via the MCP gateway)
│   ├── <drafter>.py     # LLM drafting with a deterministic demo fallback
│   ├── <checker>.py     # grounding + compliance gates (governance.grounding)
│   └── <domain tools>.py
├── data/fixtures/      # deterministic sample records for demo/CI
├── tests/              # test_tools.py + test_graph.py (run with EXTRACT_MODE=demo)
├── app.py              # Streamlit dashboard
├── docs/               # regulatory-compliance · integration-guide · aws-deployment-guide · roi-analysis
└── Dockerfile · docker-compose.yml · railway.toml · requirements.txt · .env.example · README.md
```

The workflow pattern is identical across agents: **monitor/intake → assemble
evidence (gateway tools) → reason/draft (LLM) → check (grounding + compliance) →
human gate (HITL) → act + audit**. Agent 02 also has a `demo/` folder with the
live Bedrock + real-connector path — use it as the reference for going live.

## 4. The platform you must understand first

- **LLM factory** (`llm_factory.py`): `get_llm("narrative"|"fast")` → Anthropic or
  in-account Bedrock (+ Guardrails). Demo mode bypasses it.
- **MCP authorization gateway** (`mcp_gateway/`): the governed front door. Reference
  logic for **Bedrock AgentCore Gateway + Identity**. Every tool call is
  authenticated → authorized (deny-by-default, agent-grant ∩ user-entitlement) →
  human-approved for writes → scoped-token → invoked → PHI-masked audited.
- **Connectors** (`connectors/`): fixture (offline) and live (real). `LiveSafetyConnector`
  is the worked live example. Live methods must preserve fixture signatures.
- **Governance** (`governance/`): grounding, the prompt registry, the eval harness.

## 5. Golden rules (conventions)

1. **Demo mode must always work** — every agent runs with no API key under `EXTRACT_MODE=demo`.
2. **No agent calls a vendor system directly** — always go through `gateway_tools` → the MCP gateway.
3. **HITL is framework-enforced** — graphs compile with `interrupt_before=["human_review_gate"]`; high-risk tools require a verified human approval at the gateway. Never bypass it.
4. **Set routing disposition inside a node, not in the conditional-edge path function** — LangGraph discards mutations made inside a path function.
5. **Every node appends an audit entry** (timestamp, actor, action, node).
6. **Regulated output must be grounded** — run `governance.grounding.verify_grounding` in the checker; numbers ≤ 12 are exempt; avoid ungrounded Capitalized Multi-Word phrases in demo drafters.
7. **Prompts are versioned** — register them via `governance.prompt_registry`; bump the manifest on change (see §6).
8. **Least privilege** — an agent's tool grants are its job description; keep them minimal in `mcp_gateway/policy.py`.

## 6. How to make common changes

- **Add a tool to an agent:** add the method to a connector (fixture + live), register the tool in `mcp_gateway/policy.py` (`TOOL_REGISTRY`, the agent's `AGENT_TOOL_GRANTS`, and the entitled role in `ROLE_ENTITLEMENTS`; mark `high_risk=True` for writes), wrap it in `tools/gateway_tools.py`, and call it from a node.
- **Wire a live connector:** implement the typed methods in `connectors/live.py` (mirror `LiveSafetyConnector`), resolve secrets via `get_secret`, and run with `CONNECTOR_MODE=live`. See `02-pharmacovigilance-agent/demo/DEMO-LIVE.md`.
- **Change a prompt:** edit the text, bump its version in `prompts.py`, run `python -m governance.prompt_registry --update`, and commit the manifest diff with the prompt diff. CI fails on un-bumped drift.
- **Add an eval case:** append a reviewed golden artifact + its input state to `governance/evals/golden/*.json`.
- **Add a new agent:** copy the shape of `01-regulatory-writing-agent/`, give it an id + grants in `policy.py`, and add an `aws-native-reference/<agent>/` rebuild.

## 7. Testing & CI

- Run agent tests with `EXTRACT_MODE=demo pytest tests/ -q`.
- Run the whole suite: platform (`platform_core/tests`), governance (`governance`), each `0N-*-agent/tests`, each `aws-native-reference/*/tests`.
- CI gates: tests pass, eval harness passes, prompt manifest matches, HITL-gate tests pass.
- A change is **done** when: code compiles, the agent runs end-to-end in demo mode, new/changed behavior has a test, grounding/compliance still pass, and the relevant doc is updated.

## 8. Deploying

- **Quick deploy:** `infra/cloudformation/quickstart.yaml` (see `infra/cloudformation/README.md`).
- **Container lift:** AgentCore Runtime via `aws-native-reference/_shared/runtime`.
- **Native rebuild:** Strands + Step Functions per `aws-native-reference/<agent>/DEPLOY.md`.

## 9. Where to get unstuck

`README.md` (overview) · `SUITE-STATUS.md` (state) · `ENTERPRISE-PLATFORM.md`
(architecture) · `SOLUTION-FIELD-GUIDE.md` (sales/SA) · `governance/README.md`
(controls) · `platform_core/hcls_agent_platform/mcp_gateway/README.md` (gateway) ·
`docs/SUITE-ARCHITECTURE.md` (AWS mapping) · `runbooks/` (operations).

## 10. Compliance reminder

This is a decision-support accelerator, not a validated system. AI output requires
human review and approval before any consequential action. Customers own CSV/CSA,
IdP integration, connector validation, and Guardrail configuration.
