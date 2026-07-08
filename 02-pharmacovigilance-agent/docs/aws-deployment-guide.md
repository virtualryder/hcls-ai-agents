# AWS Deployment Guide — Pharmacovigilance ICSR Intake Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore
Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account
via **Amazon Bedrock + Guardrails** — critical for ICSR source records that contain
patient PII; no content leaves the AWS account.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime` (wraps the
   compiled graph in the AgentCore container contract).
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register safety DB, MedDRA, and WHODrug as **AgentCore Gateway** targets and wire
   **AgentCore Identity** to your IdP (the gateway policy in `platform_core` is the
   reference). Mark `safety.submit_report` and `safety.write_case_draft` as high-risk
   targets requiring a human approval token.
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID` (PHI filter), `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic PV workflow steps in Lambdas (validity check, seriousness assessment,
quality check), Bedrock narrative drafting via Strands, **Step Functions** orchestration
with a `waitForTaskToken` human gate (the PV Medical Reviewer callback). Highest fidelity
to the managed, serverless target. See `aws-native-reference/01-regulatory-writing` for
the pattern; mirror for agent 02.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-pharmacovig \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=02-pharmacovigilance Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), the
AgentCore Gateway + Identity wiring, Bedrock Guardrail (PHI filter), Aurora
PostgreSQL (durable state + HITL resume), DynamoDB (append-only audit trail),
S3 Object Lock (WORM case records — GVP retention), Secrets Manager (safety DB /
MedDRA / WHODrug credentials), KMS, and CloudWatch alarms.

## PHI architecture

ICSR source records (emails, call-center transcripts, literature) contain patient PII.
The architecture keeps PHI inside the account boundary at every hop:

```
PV Processor / Reviewer Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth — token only)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ Safety DB target  → Argus/Veeva Safety (PrivateLink/VPN)
                  ├─ MedDRA target     → MSSO browser (PrivateLink or VPC endpoint)
                  └─ WHODrug target    → UMC API (VPC NAT, allowlisted egress)
Data (private subnets, KMS-encrypted):
  ├─ Aurora PostgreSQL  — case workflow state, HITL resume
  ├─ DynamoDB           — append-only audit trail (QLDB option for immutability)
  ├─ S3 Object Lock     — finalized ICSR case records (WORM, GVP retention)
  └─ Bedrock + Guardrails — private-connectivity inference via PrivateLink + PHI filter (no content egress to external AI APIs)
```

Each customer gets an isolated deployment; no shared infrastructure between tenants.

## Guardrail configuration (required in production)

The Bedrock Guardrail for this agent must include:
- **PHI filter** — block SSN, NPI, full name patterns from appearing in responses
- **Denied topics** — no clinical diagnosis recommendations, no treatment decisions
- **Word filters** — no absolute safety claims

Set `REQUIRE_BEDROCK_GUARDRAIL=1` to make the agent refuse to start without a valid
guardrail ID.
