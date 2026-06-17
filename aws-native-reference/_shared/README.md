# Shared AWS-Native Engine

Reusable pieces every agent's AWS-native deployment builds on.

## `runtime/` — Bedrock AgentCore Runtime container contract

`serve.py` + `handler.py` wrap any agent's compiled LangGraph in the AgentCore
contract (`POST /invocations`, `GET /ping`, port 8080, ARM64). Set `AGENT_MODULE`
(e.g. `agent.graph:build_regulatory_writing_graph`) and the same image runs any
agent. This is the **container lift** path: keep LangGraph, deploy managed.

## Two paths to AWS (per agent)

1. **Container lift** onto AgentCore Runtime (or ECS Fargate). Fastest; agent code
   unchanged. Inference in-account via Bedrock + Guardrails.
2. **Native rebuild** — deterministic core in Lambdas + Strands drafting on Bedrock
   + Step Functions orchestration with a `waitForTaskToken` HITL gate. Highest
   fidelity to the managed, serverless target.

## Governance on AWS

- **AgentCore Gateway + Identity** = the MCP authorization gateway (policy,
  least-privilege, scoped tokens, audit). See `infra/cloudformation/agentcore-gateway.yaml`.
- **Bedrock Guardrails** = PHI/off-label/grounding filters on inference.
- **DynamoDB (append-only)** = tamper-evident audit trail (21 CFR Part 11).
- **Step Functions `waitForTaskToken`** = framework-enforced human gate.
