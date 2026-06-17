# CloudFormation Quick Deploy

The headline AWS deployment path for the HCLS agent suite. One master template
(`quickstart.yaml`) provisions a customer-isolated environment from nested stacks.

| Template | Provisions |
|---|---|
| `network.yaml` | VPC, public/private subnets, NAT, app security group |
| `security.yaml` | KMS key, **Bedrock Guardrail** (PHI + off-label + grounding), Cognito (IdP federation), least-privilege agent role |
| `data.yaml` | Append-only **DynamoDB audit**, **S3 Object Lock** WORM store, HITL review table |
| `agentcore-gateway.yaml` | **The MCP layer: Bedrock AgentCore Gateway + AgentCore Identity** with one target per system of record |
| `agent-service.yaml` | Per-agent **Step Functions + Lambdas** (native) with a `waitForTaskToken` human gate, or AgentCore Runtime (container) |
| `quickstart.yaml` | Master — nests all of the above |

## Deploy

```bash
# 1. Stage component templates + lambda code to S3
aws s3 cp . s3://my-cfn-bucket/hcls/ --recursive --exclude "*" --include "*.yaml"
aws s3 cp ../../aws-native-reference/01-regulatory-writing/build/lambdas.zip s3://my-code-bucket/lambdas.zip

# 2. Deploy the master stack
aws cloudformation deploy \
  --template-file quickstart.yaml \
  --stack-name hcls-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      Environment=dev \
      AgentId=01-regulatory-writing \
      DeployMode=native \
      TemplateBaseUrl=https://my-cfn-bucket.s3.amazonaws.com/hcls \
      LambdaCodeBucket=my-code-bucket \
      IdpMetadataUrl=https://customer.okta.com/app/xxx/sso/saml/metadata
```

Deploy additional agents by re-running `agent-service.yaml` with a different
`AgentId`; the shared network/security/data/gateway stacks are reused.

## Notes
- `AWS::BedrockAgentCore::*` resources require an AgentCore-enabled region. Where a
  property is not yet supported, substitute the API Gateway + Lambda-authorizer +
  Cognito + STS equivalent (same semantics; see `platform_core/mcp_gateway`).
- Production: set `Environment=prod` (forces Guardrail), enable WAF on the ALB/
  CloudFront, and point `IdpMetadataUrl` at the customer IdP.
- Terraform parity lives in `../terraform`.
