# DEPLOY

## Quick Start

```bash
export EXTRACT_MODE=demo
pytest tests/ -v
```

## Production Deploy

```bash
sam build
sam deploy --guided --stack-name hcls-sitematch-agent
```

Set env vars:
- EXTRACT_MODE: demo (CI) or unset (production)
- BEDROCK_MODEL_ID: us.anthropic.claude-sonnet-4-5
- HITL_TOPIC_ARN: SNS topic for site selection lead notifications

## HITL Approval

```bash
aws stepfunctions send-task-success \
  --task-token <TOKEN> \
  --task-output '{"decision":"APPROVE_RANKING"}'
```
