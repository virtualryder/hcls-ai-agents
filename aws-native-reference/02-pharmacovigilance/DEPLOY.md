# DEPLOY — Pharmacovigilance AWS-Native Agent

## Prerequisites

- AWS CLI v2 configured with a profile that has IAM, Lambda, Step Functions, SNS, DynamoDB permissions
- AWS SAM CLI (`sam --version`)
- Python 3.11+
- Bedrock model access enabled for `us.anthropic.claude-sonnet-4-6-20260601-v1:0`
  (or set `BEDROCK_MODEL_ID` to your preferred model)

## 1  Package Lambda layer

```bash
pip install -r requirements.txt -t layer/python/
cd layer && zip -r ../layer.zip python/ && cd ..
aws lambda publish-layer-version \
  --layer-name hcls-pv-deps \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

## 2  Deploy with SAM

```bash
sam build
sam deploy --guided \
  --stack-name hcls-pv-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    HitlTopicEmail=pv-reviewer@example.com \
    BedrockModelId=us.anthropic.claude-sonnet-4-6-20260601-v1:0
```

SAM will:
- Create all five Lambda functions (assemble, draft, check, hitl_notify, finalize)
- Create a DynamoDB table for HITL task-token persistence
- Create an SNS topic and subscribe the PV Medical Reviewer email
- Register the Step Functions state machine
- Output the state machine ARN

## 3  Test a run

```bash
aws stepfunctions start-execution \
  --state-machine-arn <ARN from deploy output> \
  --input file://sample_input.json
```

Monitor in the Step Functions console. The workflow parks at
`HumanReviewGate` until the PV Medical Reviewer calls:

```bash
# Approve (submit ICSR)
aws stepfunctions send-task-success \
  --task-token <TOKEN from SNS message> \
  --task-output '{"approved": true}'

# Reject (case held, not submitted)
aws stepfunctions send-task-success \
  --task-token <TOKEN from SNS message> \
  --task-output '{"approved": false}'
```

## 4  Environment variables (Lambda)

| Variable | Default | Purpose |
|---|---|---|
| `EXTRACT_MODE` | _(unset)_ | Set to `demo` to skip Bedrock calls |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-6-20260601-v1:0` | Bedrock model ID |
| `BEDROCK_REGION` | `us-east-1` | Bedrock region |
| `BEDROCK_GUARDRAIL_ID` | _(unset)_ | Optional Bedrock Guardrail ID |
| `HITL_TOPIC_ARN` | _(unset)_ | SNS topic ARN for PV reviewer notifications |
| `REVIEW_TABLE` | _(unset)_ | DynamoDB table for task-token persistence |

## 5  Demo / CI mode

```bash
export EXTRACT_MODE=demo
pytest tests/ -v --tb=short
```

All tests pass without AWS credentials or Bedrock access.

## 6  Expedited reporting deadlines

The `Finalize` Lambda automatically sets `reporting_deadline` in the state
based on `reporting_clock_days`:

| Case type | Clock | Example deadline |
|---|---|---|
| Fatal / life-threatening, unexpected | 7 calendar days | T+7 from execution start |
| Other serious unexpected | 15 calendar days | T+15 from execution start |
| Non-serious | None | Aggregate / periodic |
