# DEPLOY — Clinical Trial Ops AWS-Native Agent

## Prerequisites

- AWS CLI v2 configured with a profile that has IAM, Lambda, Step Functions, SNS permissions
- AWS SAM CLI (`sam --version`)
- Python 3.11+
- Bedrock model access enabled for `anthropic.claude-sonnet-4-5` (or set `BEDROCK_MODEL_ID`)

## 1  Package Lambda layer

```bash
pip install -r requirements.txt -t layer/python/
cd layer && zip -r ../layer.zip python/ && cd ..
aws lambda publish-layer-version \
  --layer-name hcls-clinops-deps \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

## 2  Deploy with SAM

```bash
sam build
sam deploy --guided \
  --stack-name hcls-clinops-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    HitlTopicEmail=clinops-lead@example.com \
    BedrockModelId=us.anthropic.claude-sonnet-4-5
```

SAM will:
- Create all five Lambda functions
- Create the SNS topic and subscribe the ClinOps Lead email
- Register the Step Functions state machine
- Output the state machine ARN

## 3  Test a run

```bash
aws stepfunctions start-execution \
  --state-machine-arn <ARN from deploy output> \
  --input file://sample_input.json
```

Monitor in the Step Functions console. The workflow parks at
`HumanReviewGate` until the approver calls:

```bash
aws stepfunctions send-task-success \
  --task-token <TOKEN from SNS message> \
  --task-output '{"decision":"APPROVE_BRIEF"}'
```

## 4  Environment variables (Lambda)

| Variable | Default | Purpose |
|---|---|---|
| `EXTRACT_MODE` | _(unset)_ | Set to `demo` to skip Bedrock calls |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-5` | Bedrock model ID |
| `AWS_REGION` | `us-east-1` | Bedrock region |
| `HITL_TOPIC_ARN` | _(unset)_ | SNS topic ARN for HITL notifications |

## 5  Demo / CI mode

```bash
export EXTRACT_MODE=demo
pytest tests/ -v --tb=short
```

All tests pass without AWS credentials or Bedrock access.
