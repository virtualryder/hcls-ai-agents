# DEPLOY — Site & Patient Matching AWS-Native Agent

> **Canonical path:** for the full, current end-to-end deploy (build script,
> `GatewayMode` choice, human-gate smoke test) follow
> [`../../docs/DEPLOY-QUICKSTART.md`](../../docs/DEPLOY-QUICKSTART.md). Package with
> `scripts/build_lambdas.sh 04-site-patient-matching` — it vendors Strands + `platform_core`
> into the zip (a bare `zip` of the source `ImportError`s on cold start). The notes below
> are an agent-specific supplement.

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
