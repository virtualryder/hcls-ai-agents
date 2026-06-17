# AWS Deployment Guide — Medical Affairs MSL Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime`.
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register the CRM and MLR-approved content library as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

A Bedrock Guardrail with a **denied topics** policy (off-label promotion, unsubstantiated superiority claims) is strongly recommended as a defense-in-depth layer behind the deterministic compliance gate.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas (compliance gate, grounding check), Bedrock brief drafting via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` medical affairs approver gate. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-msl-agent \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=08-medical-affairs-msl Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail (off-label denied topics + promotional language), Aurora PostgreSQL (durable state), DynamoDB (append-only audit), S3 Object Lock (WORM brief archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
MSL / Medical Affairs Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ CRM target              → Veeva CRM / Salesforce (PrivateLink/VPN)
                  └─ Content library target  → Veeva Vault PromoMats / Zinc (PrivateLink/VPN)
Data (private subnets):
  ├─ Aurora PostgreSQL  — brief drafts, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — approved brief archive (WORM, MLR record)
  └─ Bedrock + Guardrails — in-account inference; off-label denied topics policy
```

## Connector notes

- **CRM (HCP profile read)**: configure `CRM_BASE_URL` to point to Veeva CRM or Salesforce Health Cloud. The gateway enforces read-only access for profile retrieval; the CRM write (interaction logging) is a separate gateway target that requires the approver token.
- **MLR-approved content library**: configure `CONTENT_LIBRARY_BASE_URL` to point to Veeva Vault PromoMats or equivalent. The gateway enforces that only documents with `status=APPROVED` are returned to the brief drafting context.
- **CRM interaction log write**: the finalize node writes the interaction record to the CRM only after the medical affairs approver token is verified by the gateway. This write provides the data trail for Sunshine Act reporting.
- **Bedrock Guardrail**: configure a denied-topics policy for "off-label drug promotion" and "unsubstantiated comparative claims" as a defense-in-depth layer behind the deterministic compliance gate.

See `../infra/cloudformation` and `../aws-native-reference` for the full infrastructure reference.
