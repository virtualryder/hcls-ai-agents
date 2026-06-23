# CloudFormation Quick Deploy

The headline AWS deployment path for the HCLS agent suite. One master template
(`quickstart.yaml`) provisions a customer-isolated environment from nested stacks.
For the full copy-paste walkthrough see [`../../docs/DEPLOY-QUICKSTART.md`](../../docs/DEPLOY-QUICKSTART.md).

| Template | Provisions |
|---|---|
| `network.yaml` | VPC, public/private subnets, NAT, app security group |
| `security.yaml` | KMS key, **Bedrock Guardrail** (PHI + off-label), Cognito user pool + **app client** (IdP federation), least-privilege agent role (Bedrock, DynamoDB, Secrets, KMS, Logs, Step Functions, connector invoke) |
| `data.yaml` | Append-only **DynamoDB audit**, **S3 Object Lock** WORM store, HITL review table |
| `connectors.yaml` | **One connector Lambda per system of record** — the governed backend behind every gateway target (deny-by-default via `platform_core`) |
| `gateway-portable.yaml` | **MCP layer, Path A (default):** API Gateway HTTP API + Cognito JWT authorizer. Any commercial Region. |
| `agentcore-gateway.yaml` | **MCP layer, Path B:** Bedrock AgentCore Gateway + Identity. AgentCore-enabled Regions only. |
| `agent-service.yaml` | The agent — **native** (Step Functions + Lambdas, `waitForTaskToken` human gate) or **container** (ECS Fargate, ARM64) |
| `quickstart.yaml` | Master — nests all of the above; `GatewayMode` and `DeployMode` switch the variants |

## Deploy (scripted — recommended)

```bash
scripts/build_lambdas.sh 01-regulatory-writing            # vendors deps into the zips
CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket \
  scripts/deploy.sh 01-regulatory-writing dev portable native
```

## Deploy (raw CLI)

```bash
# 1. Stage component templates + code to S3
aws s3 cp . s3://my-cfn-bucket/hcls/ --recursive --exclude "*" --include "*.yaml"
aws s3 cp ../../aws-native-reference/_shared/connector/build/connector.zip s3://my-code-bucket/connector.zip
aws s3 cp ../../aws-native-reference/01-regulatory-writing/build/lambdas.zip s3://my-code-bucket/01-regulatory-writing/lambdas.zip

# 2. Deploy the master stack
aws cloudformation deploy \
  --template-file quickstart.yaml \
  --stack-name hcls-dev-01-regulatory-writing \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      Environment=dev \
      AgentId=01-regulatory-writing \
      GatewayMode=portable \
      DeployMode=native \
      ConnectorMode=fixture \
      TemplateBaseUrl=https://my-cfn-bucket.s3.amazonaws.com/hcls \
      LambdaCodeBucket=my-code-bucket \
      LambdaCodeKey=01-regulatory-writing/lambdas.zip \
      ConnectorCodeKey=connector.zip \
      IdpMetadataUrl=https://customer.okta.com/app/xxx/sso/saml/metadata
```

Deploy additional agents by re-running with a different `AgentId`; the shared
network/security/data/connectors/gateway stacks are reused.

## Notes
- **New customer account?** Use `GatewayMode=portable` — it deploys in any commercial
  Region with no AgentCore dependency. Both gateway modes route to the same connector
  Lambdas and enforce the identical deny-by-default policy from `platform_core`.
- `AWS::BedrockAgentCore::*` (Path B) requires an AgentCore-enabled Region.
- Production: set `Environment=prod` (forces Guardrail), enable WAF on any public
  endpoint, and point `IdpMetadataUrl` at the customer IdP.
- Terraform parity lives in `../terraform`.
