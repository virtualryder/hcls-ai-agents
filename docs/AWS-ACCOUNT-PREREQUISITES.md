# AWS Account Prerequisites Checklist
### Pre-flight before deploying the HCLS AI Agent Suite

> **Run this checklist before the first CloudFormation stack deploy.** Each item is a hard dependency — missing any of them will cause deployment or runtime failures. The checklist is designed for the SI technical lead or customer cloud architect to work through together, ideally in the week before POC kickoff.

---

## How to Use This Checklist

Work through each section in order. Items marked **[BLOCKER]** will prevent deployment or first-run if not resolved. Items marked **[RECOMMENDED]** are best practice but can be deferred to Pilot stage. Items marked **[MANAGED SERVICE]** are only required if the engagement includes an ongoing managed service.

---

## Section 1 — AWS Account Setup

- [ ] **[BLOCKER]** Customer has an active AWS account (not in suspended or limit-exceeded state).
- [ ] **[BLOCKER]** Account is enrolled in AWS Organizations or is a standalone account — either is fine; document which for IAM boundary setup.
- [ ] **[BLOCKER]** AWS account has accepted the **AWS Customer Agreement** (required for Bedrock access).
- [ ] **[RECOMMENDED]** AWS account has a separate environment for POC (not sharing production account). Recommended account structure: `hcls-poc`, `hcls-pilot`, `hcls-prod` — three accounts under a single Organizations root.
- [ ] **[RECOMMENDED]** AWS Cost Anomaly Detection is enabled with a budget alert threshold appropriate for the engagement size.
- [ ] **[BLOCKER]** IAM user or role used for deployment has the following permissions:
  - `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`
  - `cloudformation:*`
  - `bedrock:*`
  - `cognito-idp:*`, `cognito-identity:*`
  - `dynamodb:*`
  - `secretsmanager:*`
  - `s3:*`
  - `ecs:*`, `ecr:*`
  - `states:*` (Step Functions)
  - `logs:*`
  - `kms:CreateKey`, `kms:EnableKeyRotation`, `kms:PutKeyPolicy`
  - `lambda:*` (used by AgentCore Gateway in some configurations)

---

## Section 2 — AWS Region Selection

- [ ] **[BLOCKER]** Deployment region is confirmed. Recommended: **`us-east-1`** (broadest Bedrock model availability + AgentCore GA). Acceptable: `us-west-2`, `eu-west-1` (GDPR), `ap-southeast-1`.
- [ ] **[BLOCKER]** Confirm the selected region has **Amazon Bedrock GA** (not preview). Check: AWS console → Bedrock → available in this region.
- [ ] **[BLOCKER]** Confirm the selected region has **Amazon Bedrock AgentCore** available. As of mid-2026: `us-east-1`, `us-west-2`, `eu-west-1`. Check current availability at the AWS Bedrock documentation page.
- [ ] **[BLOCKER]** If patient data or PHI will flow through any service, confirm the region is in a jurisdiction acceptable under the institution's data residency policy and BAA terms.
- [ ] **[RECOMMENDED]** If EU data residency is required, use `eu-west-1` (Ireland) or `eu-central-1` (Frankfurt). Confirm Bedrock and AgentCore availability in the chosen EU region before committing.

---

## Section 3 — Bedrock Model Access

Amazon Bedrock requires explicit model access requests — they are **not enabled by default**.

- [ ] **[BLOCKER]** Navigate to: AWS Console → Amazon Bedrock → Model access → Request access
- [ ] **[BLOCKER]** Request access to the following models (all required):
  - **Anthropic Claude claude-sonnet-4-6** (`anthropic.claude-sonnet-4-6-20251001`) — primary drafting and reasoning
  - **Anthropic Claude Haiku** (`anthropic.claude-haiku-4-5-20251001`) — classification steps (cost optimization)
  - **Amazon Titan Embeddings v2** — semantic search / RAG grounding (if using Bedrock Knowledge Bases)
- [ ] **[BLOCKER]** Model access approval is typically **instant for Anthropic models** in US regions, but can take 24–48 hours. Do not schedule deployment day immediately after requesting access.
- [ ] **[RECOMMENDED]** Also request: **Anthropic Claude Opus** — useful for complex regulatory reasoning tasks; not required for initial POC.
- [ ] **[RECOMMENDED]** Enable **Bedrock Guardrails** in the target region. Create a base guardrail with:
  - Content filtering: HATE, INSULTS, SEXUAL, VIOLENCE — all set to HIGH block
  - PII redaction: enable for SSN, phone, email, DOB (supplements the application-layer PHI masking)
  - Grounding: enable if using Bedrock Knowledge Bases

---

## Section 4 — AgentCore Prerequisites

- [ ] **[BLOCKER]** Navigate to: AWS Console → Amazon Bedrock → AgentCore → Enable in this region.
- [ ] **[BLOCKER]** Create an **AgentCore Gateway** resource with at least one tool schema registered. (The suite's CloudFormation template does this — verify it completes without error.)
- [ ] **[BLOCKER]** Create an **AgentCore Identity** resource linked to the Cognito User Pool created in Section 5.
- [ ] **[BLOCKER]** Verify service quota: **AgentCore concurrent agent invocations** — default is typically 10 per account/region. For a POC with multiple concurrent users, request an increase to 50+ before go-live.
- [ ] **[RECOMMENDED]** Enable **AgentCore Observability** (CloudWatch integration) — required for WAFR evidence and for the model degradation runbook.

---

## Section 5 — Amazon Cognito (Identity Provider)

- [ ] **[BLOCKER]** Create a Cognito User Pool in the target region (CloudFormation does this; verify no existing pool conflicts).
- [ ] **[BLOCKER]** Configure the User Pool with the following custom attributes (required by the gateway's `auth.py`):
  - `custom:hcls_role` — string, mutable (values: `REGULATORY_WRITER`, `PV_PROCESSOR`, `PV_MEDICAL_REVIEWER`, `CLIN_OPS_LEAD`, `SITE_SELECTION_LEAD`, `QUALIFIED_PERSON`, `PROTOCOL_DESIGNER`, `HEOR_ANALYST`, `MEDICAL_AFFAIRS_APPROVER`, `PLATFORM_ADMIN`)
  - `custom:tenant_id` — string, immutable (set at user creation; used for multi-tenant isolation)
- [ ] **[BLOCKER]** Create at least one test user per role required for the POC scope before Day 1.
- [ ] **[BLOCKER]** If the institution has an existing IdP (Okta, Azure AD, Ping), configure Cognito federation via SAML or OIDC. This is the production path; test with native Cognito users for POC if IdP federation is not ready.
- [ ] **[RECOMMENDED]** Enable MFA on the Cognito User Pool (TOTP). Required for any deployment touching PHI.
- [ ] **[RECOMMENDED]** Configure Cognito Advanced Security Mode (ASM) — adaptive authentication and anomaly detection.

---

## Section 6 — Service Quotas

Request the following quota increases **before deployment** (increases can take 24–72 hours):

| AWS Service | Quota | Default | Recommended POC | Request Path |
|---|---|---|---|---|
| Amazon Bedrock | Requests per minute (Claude Sonnet) | 60 RPM | 300 RPM | Service Quotas console → Bedrock |
| Amazon Bedrock | Tokens per minute (Claude Sonnet) | 100K TPM | 500K TPM | Service Quotas console → Bedrock |
| Amazon DynamoDB | Tables per account | 2,500 | No increase needed | — |
| AWS Step Functions | State machine executions per second | 25 | 100 | Service Quotas console → Step Functions |
| Amazon ECS (Fargate) | vCPUs per region | 256 | 256 (no change if <8 agents running) | Service Quotas console → ECS |
| AWS Secrets Manager | Secrets per region | 500 | No increase needed (8 agents = ~40 secrets) | — |
| AgentCore | Concurrent agent invocations | 10 | 50 | AWS Support case |

---

## Section 7 — Networking

- [ ] **[BLOCKER]** VPC exists in the target region (or CloudFormation will create one — confirm this is acceptable with the institution's cloud team).
- [ ] **[BLOCKER]** At least 2 private subnets in different AZs (for Fargate multi-AZ).
- [ ] **[BLOCKER]** At least 1 public subnet (for NAT Gateway or ALB, depending on whether the Streamlit app is internal or external-facing).
- [ ] **[BLOCKER]** NAT Gateway (or VPC endpoints) configured so private subnet resources can reach Bedrock, Secrets Manager, DynamoDB, and S3 without public IPs.
- [ ] **[RECOMMENDED]** VPC Endpoints for the following services (eliminates NAT Gateway traffic costs and keeps data off the public internet):
  - `com.amazonaws.<region>.bedrock-runtime`
  - `com.amazonaws.<region>.secretsmanager`
  - `com.amazonaws.<region>.dynamodb`
  - `com.amazonaws.<region>.s3`
  - `com.amazonaws.<region>.ecr.dkr` / `ecr.api`
- [ ] **[RECOMMENDED]** VPC Flow Logs enabled and retained for at least 90 days (compliance requirement for most HCLS institutions).

---

## Section 8 — Security Baseline

- [ ] **[BLOCKER]** AWS CloudTrail is enabled in the target region with S3 log delivery and at least 90-day retention.
- [ ] **[BLOCKER]** AWS Config is enabled (tracks resource configuration drift — required for Part 11 change control evidence).
- [ ] **[RECOMMENDED]** Amazon GuardDuty is enabled (threat detection; low cost; high value for CISO sign-off).
- [ ] **[RECOMMENDED]** AWS Security Hub is enabled with the `AWS Foundational Security Best Practices` standard active.
- [ ] **[RECOMMENDED]** S3 Block Public Access is enabled at the account level.

---

## Section 9 — POC Go / No-Go Verification

Run this check the day before the first live demo or user acceptance test:

```bash
# From the repo root, with AWS credentials set:
EXTRACT_MODE=demo python -m pytest governance/ platform_core/ -q

# Should output: 536 passed (or more), 0 failed
```

Then verify the live AWS path:
```bash
# Requires: Bedrock model access approved, Cognito user pool created
AWS_REGION=us-east-1 python -m pytest 02-pharmacovigilance-agent/tests/test_live.py -q -k "not slow"
```

If both pass, the environment is ready for user acceptance testing.

---

## Section 10 — Managed Service Prerequisites (Deferred to Pilot/MS Stage)

- [ ] **[MANAGED SERVICE]** AWS Health Dashboard integration (SNS alerts to SI operations team).
- [ ] **[MANAGED SERVICE]** QLDB ledger created in target region for cryptographic audit trail (Part 11 highest-assurance path).
- [ ] **[MANAGED SERVICE]** DynamoDB Point-in-Time Recovery (PITR) enabled on all tables.
- [ ] **[MANAGED SERVICE]** DynamoDB Global Tables configured if multi-region active-active is required.
- [ ] **[MANAGED SERVICE]** AWS Backup plan created covering DynamoDB, S3, and Secrets Manager.
- [ ] **[MANAGED SERVICE]** AWS Organizations Service Control Policies (SCPs) established to prevent accidental audit log deletion or KMS key disablement.
- [ ] **[MANAGED SERVICE]** AWS Support plan upgraded to at least Business (for <1 hour response time SLA on Sev-1 incidents).

---

*Related: `docs/DEPLOYMENT-HANDBOOK.md`, `docs/WELL-ARCHITECTED-REVIEW.md`, `docs/SHARED-RESPONSIBILITY-MATRIX.md`*
