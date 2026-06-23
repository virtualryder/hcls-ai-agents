# Deploy Guide — Quality CAPA Agent (AWS-native)

> **Canonical path:** for the full, current end-to-end deploy (build script,
> `GatewayMode` choice, human-gate smoke test) follow
> [`../../docs/DEPLOY-QUICKSTART.md`](../../docs/DEPLOY-QUICKSTART.md). Package with
> `scripts/build_lambdas.sh 05-quality-capa` — it vendors Strands + `platform_core`
> into the zip (a bare `zip` of the source `ImportError`s on cold start). The notes below
> are an agent-specific supplement.

## Architecture

```
EventBridge / API GW → Step Functions (quality_capa.asl.json)
  → Assemble Lambda    (classify event, build evidence corpus)
  → Draft Lambda       (Strands/Bedrock CAPA plan drafter)
  → Check Lambda       (deterministic compliance + grounding gate)
  → RouteChoice        (REVISE loop | HumanReviewGate)
  → HumanReviewGate    (waitForTaskToken — QP pauses here)
  → Finalize Lambda    (create QMS CAPA draft after QP approval)
```

## Prerequisites

- AWS account with Bedrock enabled in `us-east-1` (or override `BEDROCK_REGION`)
- Claude Sonnet model access in Bedrock
- QMS system credentials in Secrets Manager (`qms/credentials`)
- DynamoDB table for HITL review queue (`QP_REVIEW_TABLE`)
- SNS topic for QP notification (`QP_NOTIFY_TOPIC_ARN`)

## Quick deploy

```bash
# 1. Package Lambda layers
pip install strands-agents boto3 -t ./layer/python
zip -r layer.zip layer/

# 2. Deploy with SAM
sam build && sam deploy \
  --stack-name hcls-quality-capa \
  --parameter-overrides \
    BedrockRegion=us-east-1 \
    BedrockModelId=us.anthropic.claude-sonnet-4-6-20260601-v1:0 \
    BedrockGuardrailId=<your-guardrail-id> \
    ReviewTable=QP_REVIEW_TABLE \
    QmsSecretName=qms/credentials \
    QpNotifyTopicArn=arn:aws:sns:us-east-1:<account>:qp-notify \
  --capabilities CAPABILITY_IAM
```

## HITL flow

1. Finalize Lambda is NOT invoked until a QP calls `SendTaskSuccess` with their
   verified Cognito identity token.
2. The DynamoDB record stores the task token; the QP review UI reads it and
   presents the CAPA plan + compliance findings.
3. On approval, `SendTaskSuccess` resumes the state machine; on rejection,
   `SendTaskFailure` marks the execution as failed for audit.

## Environment variables (Lambda)

| Variable | Default | Description |
|---|---|---|
| `EXTRACT_MODE` | (unset) | Set `demo` for local testing without Bedrock |
| `BEDROCK_REGION` | `us-east-1` | Bedrock API region |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-6-20260601-v1:0` | Model |
| `BEDROCK_GUARDRAIL_ID` | (unset) | Guardrail ID for PHI/off-label filtering |
| `REVIEW_TABLE` | (required) | DynamoDB table for QP review queue |

## Running tests locally

```bash
EXTRACT_MODE=demo pytest tests/ -v
```
