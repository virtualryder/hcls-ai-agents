# DEPLOY — Medical Affairs MSL Agent (AWS-native)

> **Canonical path:** for the full, current end-to-end deploy (build script,
> `GatewayMode` choice, human-gate smoke test) follow
> [`../../docs/DEPLOY-QUICKSTART.md`](../../docs/DEPLOY-QUICKSTART.md). Package with
> `scripts/build_lambdas.sh 08-medical-affairs-msl` — it vendors Strands + `platform_core`
> into the zip (a bare `zip` of the source `ImportError`s on cold start). The notes below
> are an agent-specific supplement.

## Prerequisites
- AWS account with Bedrock access (Claude Sonnet in us-east-1)
- SAM CLI or CDK
- DynamoDB table for HITL task tokens (`REVIEW_TABLE`)
- Optional: Bedrock Guardrail for off-label, promotional, and PHI filtering

## Lambdas

| Lambda | Handler | Role |
|---|---|---|
| `Assemble` | `lambdas/assemble.handler` | Read CRM (HCP profile) + DMS (approved docs) |
| `Draft` | `lambdas/draft.handler` | Bedrock InvokeModel |
| `Check` | `lambdas/check.handler` | No external calls |
| `HitlNotify` | `lambdas/hitl_notify.handler` | DynamoDB write + SNS |
| `Finalize` | `lambdas/finalize.handler` | MLR gateway write (HIGH-RISK) |

## Environment variables

| Variable | Description |
|---|---|
| `EXTRACT_MODE` | Set to `demo` for no-AWS local testing |
| `BEDROCK_MODEL_ID` | Claude model ID (default: claude-sonnet-4-6) |
| `BEDROCK_REGION` | AWS region (default: us-east-1) |
| `BEDROCK_GUARDRAIL_ID` | Guardrail ID — off-label + promotional filter REQUIRED in prod |
| `REVIEW_TABLE` | DynamoDB table for HITL task tokens |

## Step Functions

Deploy `stepfunctions/medical_affairs_msl.asl.json` via CloudFormation or CDK.
Substitute Lambda ARNs for `${AssembleFunctionArn}`, `${DraftFunctionArn}`,
`${CheckFunctionArn}`, `${HitlNotifyFunctionArn}`, `${FinalizeFunctionArn}`.

## HITL flow (Medical Affairs Approver)

1. Execution pauses at `HumanReviewGate` (`waitForTaskToken`).
2. `HitlNotify` stores the token and notifies the Medical Affairs Approver.
3. The Approver reviews the brief + compliance findings in the review UI.
4. If compliant: Approver calls `SendTaskSuccess` with their verified identity.
5. If non-compliant (off-label / escalation): Approver calls `SendTaskFailure`.
6. Step Functions resumes → `Finalize` submits to MLR (HIGH-RISK write, approved path only).

## Bedrock Guardrail (REQUIRED in production)

Configure a Guardrail with:
- **Denied topics**: off-label drug use, comparative efficacy claims not in labeling
- **Word filters**: "off-label", "best-in-class", "superior to all"
- **PHI masking**: enabled

Set `BEDROCK_GUARDRAIL_ID` and `BEDROCK_GUARDRAIL_VERSION`.

## Testing locally

```bash
export EXTRACT_MODE=demo
cd tests && python -m pytest -q
```
