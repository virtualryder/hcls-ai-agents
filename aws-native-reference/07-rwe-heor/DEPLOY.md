# DEPLOY — RWE/HEOR Agent (AWS-native)

> **Canonical path:** for the full, current end-to-end deploy (build script,
> `GatewayMode` choice, human-gate smoke test) follow
> [`../../docs/DEPLOY-QUICKSTART.md`](../../docs/DEPLOY-QUICKSTART.md). Package with
> `scripts/build_lambdas.sh 07-rwe-heor` — it vendors Strands + `platform_core`
> into the zip (a bare `zip` of the source `ImportError`s on cold start). The notes below
> are an agent-specific supplement.

## Prerequisites
- AWS account with Bedrock access (Claude Sonnet in us-east-1)
- SAM CLI or CDK
- DynamoDB table for HITL task tokens (`REVIEW_TABLE`)
- Optional: Bedrock Guardrail for causal-claim and statistical-fabrication filtering

## Lambdas

| Lambda | Handler | Role |
|---|---|---|
| `Assemble` | `lambdas/assemble.handler` | Read RWD query results |
| `Synthesize` | `lambdas/draft.handler` | Bedrock InvokeModel |
| `Check` | `lambdas/check.handler` | No external calls |
| `HitlNotify` | `lambdas/hitl_notify.handler` | DynamoDB write + SNS |
| `Finalize` | `lambdas/finalize.handler` | Evidence repo write |

## Environment variables

| Variable | Description |
|---|---|
| `EXTRACT_MODE` | Set to `demo` for no-AWS local testing |
| `BEDROCK_MODEL_ID` | Claude model ID (default: claude-sonnet-4-6) |
| `BEDROCK_REGION` | AWS region (default: us-east-1) |
| `BEDROCK_GUARDRAIL_ID` | Optional: Bedrock Guardrail ID |
| `REVIEW_TABLE` | DynamoDB table for HITL task tokens |

## Step Functions

Deploy `stepfunctions/rwe_heor.asl.json` via CloudFormation or CDK.
Substitute Lambda ARNs for `${AssembleFunctionArn}`, `${SynthesizeFunctionArn}`,
`${CheckFunctionArn}`, `${HitlNotifyFunctionArn}`, `${FinalizeFunctionArn}`.

## HITL flow

1. Execution pauses at `HumanReviewGate` (`waitForTaskToken`).
2. `HitlNotify` stores the token and notifies the Epidemiologist via SNS/EventBridge.
3. The Epidemiologist reviews in the review UI and calls `SendTaskSuccess` (approve)
   or `SendTaskFailure` (reject) with their verified identity.
4. Step Functions resumes → `Finalize` publishes the evidence package.

## Testing locally

```bash
export EXTRACT_MODE=demo
cd tests && python -m pytest -q
```
