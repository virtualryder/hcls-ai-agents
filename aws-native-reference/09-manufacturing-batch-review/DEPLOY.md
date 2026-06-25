# Deploy — Agent 09 (AWS-native, Manufacturing Batch-Review)

Per-customer, validated AWS account. The agent reuses the suite's shared CloudFormation
quick-deploy; this native path adds the Strands Lambdas + the Step Functions state machine.

## Prerequisites
- Bedrock model access in-Region (+ a Guardrail in production).
- IdP roles `MFG_OPERATOR` and `QA_RELEASE` federated through Cognito (`AUTH_ROLE_CLAIM`).
- Private connectivity to MES + LIMS (PrivateLink / Direct Connect); connector targets `mes`, `lims`.

## Build + deploy
```bash
make build-lambdas                                  # vendors deps into each zip
CFN_BUCKET=my-cfn CODE_BUCKET=my-code \
  scripts/deploy.sh 09-manufacturing-batch-review dev portable native
```
This provisions: per-customer VPC + KMS CMK, Cognito SAML→JWT, dual MCP gateway, the connector
Lambdas (incl. `mes`/`lims` targets), the five batch-review Lambdas, the Step Functions state
machine with the QA `waitForTaskToken` gate, S3 Object Lock + DynamoDB append-only audit.

## The QA gate (framework-enforced HITL)
`QAReviewGate` is `arn:aws:states:::lambda:invoke.waitForTaskToken` with a 14-day timeout. Execution
pauses; `hitl_notify` persists the task token + notifies QA. A QA reviewer's UI calls
`SendTaskSuccess` with `{approved, decision: RELEASE|HOLD, reviewer, disposition_id}`; `finalize` then
records the disposition. No batch is released without that signed approval.

## Smoke test (no AWS)
```bash
EXTRACT_MODE=demo python3 -c "import json,sys; sys.path.insert(0,'aws-native-reference/09-manufacturing-batch-review/lambdas'); \
import assemble,draft,check; \
b=json.load(open('aws-native-reference/09-manufacturing-batch-review/sample_input.json')); \
s=json.loads(assemble.handler({'body':b})['body']); s=json.loads(draft.handler({'body':s})['body']); \
s=json.loads(check.handler({'body':s})['body']); print(s['routing']['action'], s['disposition_recommendation'])"
```
