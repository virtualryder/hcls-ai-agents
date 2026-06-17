# Deploy All Agents

Shared stacks once, then one service stack per agent.

## 1. Shared environment (once per customer/env)
Deploy `quickstart.yaml` with `AgentId=01-regulatory-writing`. This creates the
network, security (KMS + Guardrail + Cognito), data (audit/WORM/review), and the
AgentCore Gateway — plus the first agent.

## 2. Each additional agent
Package that agent's `lambdas.zip` (native) or build/push its AgentCore Runtime
image (container), then deploy `agent-service.yaml`:

```bash
for AGENT in 02-pharmacovigilance 03-clinical-trial-ops 04-site-patient-matching \
             05-quality-capa 06-protocol-design 07-rwe-heor 08-medical-affairs-msl; do
  aws cloudformation deploy \
    --template-file ../infra/cloudformation/agent-service.yaml \
    --stack-name hcls-dev-$AGENT \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=dev AgentId=$AGENT DeployMode=native \
      LambdaCodeBucket=my-code-bucket LambdaCodeKey=$AGENT/lambdas.zip \
      AgentExecutionRoleArn=<from-security-stack> \
      BedrockGuardrailId=<from-security-stack> \
      ReviewTableName=<from-data-stack>
done
```

## 3. Register gateway targets
Add each system of record this agent uses as an AgentCore Gateway target
(`agentcore-gateway.yaml`), matching the agent's grants in
`platform_core/mcp_gateway/policy.py`.

## 4. Validate
Run each agent's `tests/` and the suite `governance/` evals as CSV evidence before
promoting an environment to `prod`.
