# AWS Deployment Guide — Protocol Design Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference is served by **Amazon Bedrock + Guardrails**, reached from the account VPC over **AWS PrivateLink** (a regional AWS service reached privately, not in-VPC hosting).

1. Build the ARM64 image from `aws-native-reference/_shared/runtime`.
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register the guidance library DMS and RWD platform as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock protocol drafting via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` medical reviewer gate. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-protocol-design \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=06-protocol-design Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail, Aurora PostgreSQL (durable state), DynamoDB (append-only audit), S3 Object Lock (WORM protocol archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
Clinical Scientist Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ Guidance DMS target → Veeva Vault / internal DMS (PrivateLink/VPN)
                  └─ RWD platform target → TriNetX / Flatiron (PrivateLink/API)
Data (private subnets):
  ├─ Aurora PostgreSQL  — protocol drafts, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — finalized protocol drafts (WORM)
  └─ Bedrock + Guardrails — private-connectivity inference via PrivateLink
```

## Connector notes

- **Guidance library**: configure `GUIDANCE_DMS_BASE_URL` to point to Veeva Vault or an internal document management system that hosts ICH and FDA guidance documents. The guidance retrieval tool performs semantic search over the library index.
- **RWD platform**: aggregate-only cohort queries; configure `RWD_BASE_URL` and enforce de-identification contract at the gateway layer.
- **DMS write (finalize)**: the finalize node saves the approved protocol draft to the DMS only after the medical reviewer approval token is verified by the gateway. Configure `PROTOCOL_DMS_WRITE_URL` and the write credential in Secrets Manager.

See `../infra/cloudformation` and `../aws-native-reference` for the full infrastructure reference.
