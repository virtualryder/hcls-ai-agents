# AWS Deployment Guide — RWE & HEOR Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime`.
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register the RWD platforms, literature API, and dossier system as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock evidence synthesis via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` reviewer gate. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-rwe-heor \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=07-rwe-heor Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail (PHI detection), Aurora PostgreSQL (durable state), DynamoDB (append-only audit), S3 Object Lock (WORM evidence archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
HEOR Analyst Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ RWD platform targets → IQVIA / Optum / TriNetX (PrivateLink/API)
                  ├─ Literature API target → PubMed / Embase (public API / licensed)
                  └─ Dossier system target → Veeva Vault / submissions platform (PrivateLink/VPN)
Data (private subnets):
  ├─ Aurora PostgreSQL  — evidence summaries, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — finalized evidence packages (WORM)
  └─ Bedrock + Guardrails — in-account inference, PHI detection
```

## Connector notes

- **RWD platforms**: enforce aggregate-only query contracts at the gateway layer. Configure `RWD_BASE_URL` and API credentials per platform in Secrets Manager. The gateway policy rejects any response containing patient-level identifiers.
- **Literature API**: PubMed E-utilities API is publicly accessible; Embase and Cochrane require licensed API keys. Configure `LITERATURE_API_BASE_URL` and `LITERATURE_API_KEY` in Secrets Manager.
- **Dossier system**: the finalize node saves the approved evidence summary only after the reviewer approval token is verified by the gateway. Configure `DOSSIER_WRITE_URL` and the write credential in Secrets Manager.

See `../infra/cloudformation` and `../aws-native-reference` for the full infrastructure reference.
