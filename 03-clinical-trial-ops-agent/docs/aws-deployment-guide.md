# AWS Deployment Guide — Clinical Trial Operations Agent

> **Full console-level walkthrough (click-by-click + CLI):** see [`../../docs/DEPLOYMENT-HANDBOOK.md`](../../docs/DEPLOYMENT-HANDBOOK.md). This file is the summary.


Two paths, both documented suite-wide. Pick based on how managed you want it.

## Path A — Container lift onto Bedrock AgentCore Runtime (fastest)

Keep the LangGraph agent; containerize it and run on **Amazon Bedrock AgentCore Runtime** (ARM64, `/invocations` + `/ping`, port 8080). Inference runs in-account via **Amazon Bedrock + Guardrails**.

1. Build the ARM64 image from `aws-native-reference/_shared/runtime` (wraps the compiled graph in the AgentCore container contract).
2. Push to ECR; create the AgentCore Runtime; attach the execution role.
3. Register CTMS, eTMF, and EDC systems as **AgentCore Gateway** targets and wire **AgentCore Identity** to your IdP (the gateway policy in `platform_core` is the reference).
4. Set `LLM_PROVIDER=bedrock`, `BEDROCK_GUARDRAIL_ID`, `CONNECTOR_MODE=live`.

## Path B — Native rebuild (Strands + Step Functions)

Deterministic core in Lambdas, Bedrock drafting via Strands SDK, **Step Functions** orchestration with a `waitForTaskToken` human gate for the ClinOps Lead review step. See `aws-native-reference/` for the structural pattern.

## Quick deploy (CloudFormation)

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/quickstart.yaml \
  --stack-name hcls-clinops \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AgentId=03-clinical-trial-ops Environment=dev
```

This provisions: VPC + private subnets, ECS Fargate (UI + agent worker), AgentCore Gateway + Identity wiring, Bedrock Guardrail (PHI scrubbing), Aurora PostgreSQL (durable state), DynamoDB (append-only audit), S3 Object Lock (WORM briefing archive), Secrets Manager, KMS, and CloudWatch alarms.

## Reference data architecture

```
ClinOps Team Browser
  └─ CloudFront + WAF
       └─ ALB (Cognito/Okta auth)
            ├─ ECS Fargate — Streamlit UI
            ├─ ECS Fargate — LangGraph agent worker
            └─ AgentCore Gateway (+ Identity)
                  ├─ CTMS target   → Medidata / Veeva CTMS (PrivateLink/VPN)
                  ├─ eTMF target   → Veeva Vault eTMF (PrivateLink/VPN)
                  └─ EDC target    → Medidata Rave / Oracle (PrivateLink/VPN)
Data (private subnets):
  ├─ Aurora PostgreSQL  — briefings, workflow state
  ├─ DynamoDB           — append-only audit trail (21 CFR Part 11)
  ├─ S3 Object Lock     — finalized briefings (WORM)
  └─ Bedrock + Guardrails — private-connectivity inference via PrivateLink, PHI scrubbing
```

Each customer deployment is isolated; no shared infrastructure between sponsors or studies.

## Connector notes

- **CTMS**: REST or SOAP; Medidata Rave CTMS and Veeva Vault CTMS both expose study enrollment and site-status endpoints. Configure `CTMS_BASE_URL` and credentials in Secrets Manager.
- **eTMF**: Veeva Vault document API or TMF Reference Model-aligned REST endpoints. Configure `ETMF_BASE_URL`.
- **EDC**: Medidata Web Services API or Oracle Clinical One REST API. EDC writes (query creation) require the ClinOps Lead approval token from the human gate before the gateway allows the call.

See `../infra/cloudformation` for the full stack templates and `../aws-native-reference` for the serverless-native architecture reference.
