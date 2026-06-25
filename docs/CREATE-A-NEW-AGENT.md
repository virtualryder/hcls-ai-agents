# Creating a New Agent

The suite is a template, not a dead end. A ninth agent reuses the same governed control
plane (gateway, PHI masking, grounding, HITL, audit) and the same deck system — you add
workflow-specific logic, fixtures, and content, not new infrastructure.

## 1. Scaffold the agent package

Copy the closest existing agent (e.g. `01-regulatory-writing-agent/` for a
document/drafting workflow, `02-pharmacovigilance-agent/` for a case-intake workflow) to
`NN-your-agent/` and keep the structure:

```
NN-your-agent/
├── agent/            # LangGraph workflow
│   ├── graph.py      #   nodes wired into a graph with interrupt_before the HUMAN gate
│   ├── nodes.py      #   one function per pipeline step
│   ├── state.py      #   typed state object
│   ├── prompts.py    #   prompts (registered + hash-pinned in governance/)
│   └── persistence.py
├── tools/            # gateway-backed tools + a demo-fallback drafter + a grounding/compliance checker
├── data/fixtures/    # 3 realistic, de-identified records for demo mode
├── tests/            # flagship-level suite (graph, tools, HITL gate)
├── docs/             # regulatory-compliance, integration-guide, aws-deployment-guide, roi-analysis
├── app.py            # Streamlit dashboard
├── Dockerfile · docker-compose.yml · requirements.txt · .env.example
```

## 2. Wire it to the platform (do not re-implement controls)

- **Tools call the gateway, never a vendor API directly.** Use `platform_core/hcls_agent_platform/mcp_gateway`; name tools `connector_kind.operation` so they map 1:1 to AgentCore Gateway targets.
- **Mask first.** Route inputs through the PHI masker before any model call or audit write.
- **Gate the consequential step.** Use `interrupt_before` (LangGraph) / `waitForTaskToken` (Step Functions) so the consequential action blocks until a named, correctly-roled reviewer binds identity. Define the bright line: *what the agent must never decide.*
- **Ground every regulated claim.** Add a grounding/compliance checker that fails fast when a figure has no source.
- **Audit everything.** Every node writes to the append-only audit with model + prompt version.

## 3. Register prompts and add governance coverage

- Add prompts to `governance/prompt_manifest.json` (hash-pinned; CI fails on un-bumped drift).
- Add a golden-artifact eval to `governance/evals/`, a HITL-gate test, and at least one red-team scenario (`governance/redteam/`).

## 4. Add the AWS-native rebuild

Mirror the agent under `aws-native-reference/NN-your-agent/` (Strands agent + Step Functions
ASL with a `waitForTaskToken` human gate + Lambda handlers + `DEPLOY.md`). Reuse the shared
connector handler in `aws-native-reference/_shared/`.

## 5. Wire deployment

- Confirm the connector kind is covered by `infra/cloudformation/connectors.yaml` (add a target if new).
- The agent deploys through the existing CloudFormation quickstart and `scripts/build_lambdas.sh` / `scripts/deploy.sh` — no new master template needed.

## 6. Add it to the deck system

In `decks/build-agent-decks.js`, append a content object to the `AGENTS` array following the
contract in `gtm/DECK-CONTENT-SPEC.md`: `hero`, `valueProp`, three `hookStats`, `issueBullets`,
`costBig` + `costMath` + `costRisks` + `costTag`, `brightLine`, the five-step `pipeline`, the
`arch` block, four `proofStats`, six `deploySteps`, `deployOneLiner`, and speaker notes. Add the
filename to `fileNames`, the short name to the overview's `shortNames`, and include the index in a
`portfolioSlide([...])` call. **Every new stat must first be added to `gtm/HCLS-DECK-SOURCES.md`
with a source-class tag and URL** — keep `costBig` short (one line). Regenerate with
`node decks/build-agent-decks.js`.

## 7. Verify

`pytest NN-your-agent/tests -q` (demo mode, no API key), run the eval harness, exercise the HITL
gate, and confirm CI (`.github/workflows/ci.yml`) stays green. Then render the new deck and check
text fit.

## Definition of done (flagship depth)

A full LangGraph workflow with a framework-enforced human gate · gateway-backed tools + a
demo-fallback drafter + a grounding checker · 3 deterministic fixtures · a flagship-level test
suite · a Streamlit dashboard · a four-document doc set · an AWS-native rebuild · a cited 6-slide
deck. Position it honestly on the maturity ladder (Documented → Demonstrated → Deployable →
Production-ready).
