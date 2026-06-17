# Deploy Guide — Protocol Design Agent (AWS-native)

## Architecture

```
API GW / EventBridge → Step Functions (protocol_design.asl.json)
  → Assemble Lambda      (build evidence corpus from guidance + RWD data)
  → Draft Lambda         (Strands/Bedrock protocol section drafter)
  → Check Lambda         (deterministic compliance + grounding gate)
  → RouteChoice          (REVISE loop | HumanReviewGate)
  → HumanReviewGate      (waitForTaskToken — Medical/Clinical Reviewer pauses here)
  → Finalize Lambda      (package protocol for IND/CTA after reviewer approval)
```

## Prerequisites

- AWS account with Bedrock enabled in `us-east-1` (or override `BEDROCK_REGION`)
- Claude Sonnet model access in Bedrock
- RIM connector credentials in Secrets Manager (`rim/credentials`)
- RWD connector credentials in Secrets Manager (`rwd/credentials`)
- DynamoDB table for HITL review queue (`REVIEWER_TABLE`)
- SNS topic for reviewer notification (`REVIEWER_NOTIFY_TOPIC_ARN`)

## Quick deploy

```bash
# 1. Package Lambda layers
pip install strands-agents boto3 -t ./layer/python
zip -r layer.zip layer/

# 2. Deploy with SAM
sam build && sam deploy \
  --stack-name hcls-protocol-design \
  --parameter-overrides \
    BedrockRegion=us-east-1 \
    BedrockModelId=us.anthropic.claude-sonnet-4-6-20260601-v1:0 \
    BedrockGuardrailId=<your-guardrail-id> \
    ReviewTable=REVIEWER_TABLE \
    RimSecretName=rim/credentials \
    RwdSecretName=rwd/credentials \
    ReviewerNotifyTopicArn=arn:aws:sns:us-east-1:<account>:reviewer-notify \
  --capabilities CAPABILITY_IAM
```

## HITL flow

1. Finalize Lambda is NOT invoked until a Medical/Clinical Reviewer calls
   `SendTaskSuccess` with their verified Cognito identity token.
2. The DynamoDB record stores the task token; the reviewer UI reads it and
   presents the draft protocol + compliance findings + regulatory risks.
3. On approval, `SendTaskSuccess` resumes the state machine with the reviewer's
   identity bound into the audit trail.

## Environment variables (Lambda)

| Variable | Default | Description |
|---|---|---|
| `EXTRACT_MODE` | (unset) | Set `demo` for local testing without Bedrock |
| `BEDROCK_REGION` | `us-east-1` | Bedrock API region |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-6-20260601-v1:0` | Model |
| `BEDROCK_GUARDRAIL_ID` | (unset) | Guardrail ID for PHI/off-label filtering |
| `REVIEW_TABLE` | (required) | DynamoDB table for reviewer queue |

## Running tests locally

```bash
EXTRACT_MODE=demo pytest tests/ -v
```
