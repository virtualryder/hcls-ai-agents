# AWS Deployment Guide — Quality & CAPA Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime`.
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register the QMS and ERP/MES systems as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock CAPA drafting via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` QP review gate. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-quality-capa \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=05-quality-capa Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail, Aurora PostgreSQL (durable state), DynamoDB (append-only audit, 21 CFR Part 11), S3 Object Lock (WORM CAPA record archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
QA Team Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ QMS target    → Veeva Vault QMS / MasterControl (PrivateLink/VPN)
                  └─ ERP target    → SAP / Oracle (PrivateLink/VPN)
Data (private subnets):
  ├─ Aurora PostgreSQL  — CAPA drafts, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — finalized CAPA records (WORM)
  └─ Bedrock + Guardrails — private-connectivity inference via PrivateLink
```

## Connector notes

- **QMS**: Veeva Vault QMS exposes a REST API for complaint, deviation, and CAPA record retrieval. MasterControl and Pilgrim SmartSolve expose SOAP or REST APIs. Configure `QMS_BASE_URL` and credentials in Secrets Manager. QMS record creation (finalize node) requires the QP approval token from the human gate.
- **ERP/MES**: lot and batch record lookups for material traceability. Configure `ERP_BASE_URL`.
- **Notifications**: the finalize node can trigger SNS/SES notifications to the QP and affected site managers upon CAPA record creation.

See `../infra/cloudformation` and `../aws-native-reference` for the full infrastructure reference.
