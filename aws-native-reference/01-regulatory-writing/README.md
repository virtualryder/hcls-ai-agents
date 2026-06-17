# AWS-Native: Regulatory Writing (Agent 01)

Two deployable paths for Agent 01 on AWS.

## Container lift (AgentCore Runtime / ECS Fargate)
Use the shared runtime (`../_shared/runtime`) to wrap the LangGraph agent in the
AgentCore contract. Set `AGENT_MODULE=agent.graph:build_regulatory_writing_graph`,
`LLM_PROVIDER=bedrock`, `CONNECTOR_MODE=live`. Fastest; agent code unchanged.

## Native rebuild (Strands + Step Functions)
- `core.py` — deterministic evidence/compliance/grounding + routing (unit-tested).
- `strands_agent.py` — Bedrock drafting via Strands (demo fallback).
- `lambdas/` — assemble · draft · check · hitl_notify · finalize.
- `stepfunctions/regulatory_writing.asl.json` — orchestration with a
  `waitForTaskToken` Regulatory-Approver gate.

Run the deterministic tests with no AWS:

```bash
cd aws-native-reference/01-regulatory-writing
EXTRACT_MODE=demo pytest tests/ -q
```

Deploy: see [DEPLOY.md](./DEPLOY.md) and `infra/cloudformation`.
