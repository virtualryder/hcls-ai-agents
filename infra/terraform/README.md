# Terraform — reference skeleton (NOT parity)

> **Status:** reference skeleton, **not** at parity with CloudFormation. See [`../../docs/TERRAFORM-AND-GOVCLOUD-STATUS.md`](../../docs/TERRAFORM-AND-GOVCLOUD-STATUS.md).

CloudFormation in `../cloudformation` is the **headline** quick-deploy path for
this suite. This Terraform tree is maintained for parity for customers standardized
on Terraform. It mirrors the same stacks:

```
infra/terraform/
├── envs/dev/            # root module: wires the modules for an environment
└── modules/
    ├── network/         # VPC, subnets, NAT, SGs
    ├── security/        # KMS, Bedrock Guardrail, Cognito, IAM
    ├── data/            # DynamoDB (audit), S3 Object Lock, review table
    └── agent_service/   # Step Functions + Lambdas (native) / AgentCore Runtime
```

The control semantics are identical to CloudFormation: AgentCore Gateway + Identity
for the MCP layer, Guardrails on inference, append-only audit, WORM store, and a
`waitForTaskToken` human gate. Use one IaC tool per customer — not both.

```bash
cd envs/dev
terraform init && terraform plan -var environment=dev -var agent_id=01-regulatory-writing
```
