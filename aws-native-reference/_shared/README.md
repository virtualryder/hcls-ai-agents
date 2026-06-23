# Shared AWS-Native Engine

Reusable pieces every agent's AWS-native deployment builds on.

## `runtime/` — Bedrock AgentCore Runtime container contract

`serve.py` + `handler.py` wrap any agent's compiled LangGraph in the AgentCore
contract (`POST /invocations`, `GET /ping`, port 8080, ARM64). Set `AGENT_MODULE`
(e.g. `agent.graph:build_regulatory_writing_graph`) and the same image runs any
agent. This is the **container lift** path: keep LangGraph, deploy managed.

## `connector/` — the governed backend behind every gateway target

`handler.py` is the Lambda that sits behind each MCP gateway *target* (one per system
of record). It runs every call through `platform_core`'s `MCPGateway`, so the
deny-by-default authorization, least-privilege intersection, human-approval gate,
scoped token, and append-only audit are the **tested Python reference**, not a
re-implementation. The same handler serves **both** gateway modes — Bedrock AgentCore
Gateway (`infra/cloudformation/agentcore-gateway.yaml`) and the portable API Gateway
(`gateway-portable.yaml`) — keyed by the `CONNECTOR_KIND` env var. Packaged into
`connector.zip` by `scripts/build_lambdas.sh`.

## Two paths to AWS (per agent)

1. **Container lift** onto AgentCore Runtime (or ECS Fargate). Fastest; agent code
   unchanged. Inference in-account via Bedrock + Guardrails.
2. **Native rebuild** — deterministic core in Lambdas + Strands drafting on Bedrock
   + Step Functions orchestration with a `waitForTaskToken` HITL gate. Highest
   fidelity to the managed, serverless target.

## Governance on AWS

- **MCP authorization gateway** (policy, least-privilege, scoped tokens, audit) in two
  interchangeable forms: Bedrock **AgentCore Gateway + Identity**
  (`infra/cloudformation/agentcore-gateway.yaml`) or the portable **API Gateway + Cognito
  JWT authorizer** (`gateway-portable.yaml`). Both front the same `connector/` Lambdas.
- **Bedrock Guardrails** = PHI/off-label/grounding filters on inference.
- **DynamoDB (append-only)** = tamper-evident audit trail (21 CFR Part 11).
- **Step Functions `waitForTaskToken`** = framework-enforced human gate.
