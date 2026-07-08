# AWS Deployment Guide — Regulatory Writing Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore
Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account
via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime` (wraps the
   compiled graph in the AgentCore container contract).
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register systems of record as **AgentCore Gateway** targets and wire **AgentCore
   Identity** to your IdP (the gateway policy in `platform_core` is the reference).
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock drafting via Strands, **Step Functions**
orchestration with a `waitForTaskToken` human gate. Highest fidelity to the
managed, serverless target. See `aws-native-reference/01-regulatory-writing`.

## Quick deploy (CloudFormation)

The headline path is CloudFormation nested stacks in `infra/cloudformation`:

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-regwriting \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=01-regulatory-writing Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), the
AgentCore Gateway + Identity wiring, Bedrock Guardrail, Aurora PostgreSQL
(durable state), DynamoDB (append-only audit), S3 Object Lock (WORM submission
drafts), Secrets Manager, KMS, and CloudWatch alarms. Terraform parity lives in
`infra/terraform`.

## Reference data architecture

```
Author/Approver Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ RIM target  → Veeva Vault RIM (PrivateLink/VPN)
                  └─ DMS target  → Veeva Vault / OpenText
Data (private subnets):
  ├─ Aurora PostgreSQL  — drafts, workflow state
  ├─ DynamoDB           — append-only audit trail
  ├─ S3 Object Lock     — finalized submission drafts (WORM)
  └─ Bedrock + Guardrails — private-connectivity inference via PrivateLink (no content egress to external AI APIs)
```

Each customer gets an isolated deployment; no shared infrastructure between tenants.
