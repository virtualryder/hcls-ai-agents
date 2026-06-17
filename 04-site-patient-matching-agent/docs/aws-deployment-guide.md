# AWS Deployment Guide — Site & Patient Matching Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime`.
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register the site registry and RWD platform as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock report drafting via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` human gate for clinical lead review. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-site-matching \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=04-site-patient-matching Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail (PHI detection), Aurora PostgreSQL (durable state), DynamoDB (append-only audit), S3 Object Lock (WORM report archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
Clinical Team Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ Site registry target  → CTMS / internal DB (PrivateLink/VPN)
                  └─ RWD platform target   → TriNetX / Flatiron / IQVIA (PrivateLink/API)
Data (private subnets):
  ├─ Aurora PostgreSQL  — reports, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — finalized feasibility reports (WORM)
  └─ Bedrock + Guardrails — in-account inference, PHI detection layer
```

## Connector notes

- **RWD platform**: configure the gateway to enforce aggregate-only query contracts. TriNetX, Flatiron, and IQVIA all expose REST APIs for de-identified cohort queries; set `RWD_BASE_URL` and API credentials in Secrets Manager. The gateway policy rejects any response containing patient-level identifiers.
- **Site registry**: typically the CTMS site module or an internal site capability database. Configure `SITE_REGISTRY_BASE_URL`.
- **Outreach workflow**: the finalize node triggers a site notification workflow (e.g., Salesforce, Veeva CRM, or a simple SES email) only after the clinical lead approval token is verified by the gateway.

See `../infra/cloudformation` and `../aws-native-reference` for the full infrastructure reference.
