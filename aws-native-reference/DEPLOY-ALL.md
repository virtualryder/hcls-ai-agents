# Deploy All Agents

Shared stacks once, then one service stack per agent. Full walkthrough:
[`../docs/DEPLOY-QUICKSTART.md`](../docs/DEPLOY-QUICKSTART.md).

## 0. Build the code bundles (deps vendored in)
```bash
scripts/build_lambdas.sh           # all agents' lambdas.zip + the shared connector.zip
```

## 1. Shared environment + first agent (once per customer/env)
```bash
CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket \
  scripts/deploy.sh 01-regulatory-writing dev portable native
```
This creates the network, security (KMS + Guardrail + Cognito + app client + role),
data (audit/WORM/review), the **connector Lambdas**, the **MCP gateway**
(`portable` API Gateway or `agentcore`), and the first agent.

## 2. Each additional agent
The shared stacks are reused; only the agent service is per-agent:
```bash
for AGENT in 02-pharmacovigilance 03-clinical-trial-ops 04-site-patient-matching \
             05-quality-capa 06-protocol-design 07-rwe-heor 08-medical-affairs-msl; do
  scripts/build_lambdas.sh $AGENT
  CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket \
    scripts/deploy.sh $AGENT dev portable native
done
```

## 3. Gateway targets
Every system of record already has a connector Lambda + gateway target (created by
`connectors.yaml` + the gateway stack). Each agent's allowed tools are governed by
`platform_core/mcp_gateway/policy.py:AGENT_TOOL_GRANTS` — no per-agent gateway edit needed.

## 4. Validate
Run each agent's `tests/` and the suite `governance/` evals as CSV evidence before
promoting an environment to `prod`. Smoke-test the human gate per
`docs/DEPLOY-QUICKSTART.md` §6.
