# Agent 09 — AWS Deployment Guide

The agent inherits the suite's shared control plane and one-command deploy path. Two runtimes are
available, identical to the other agents:

- **Container (AgentCore Runtime / ECS Fargate, ARM64).** The Streamlit/agent service runs in a
  per-customer VPC; see the repo `docs/DEPLOY-QUICKSTART.md` and `infra/cloudformation/`.
- **AWS-native (Strands + Step Functions).** `aws-native-reference/09-manufacturing-batch-review/`
  — Lambda-per-step state machine with a `waitForTaskToken` QA gate. See its `DEPLOY.md`.

## What the customer provides
- An IdP (Okta / Entra / Ping) with the `MFG_OPERATOR` and `QA_RELEASE` roles.
- Private connectivity to MES and LIMS (PrivateLink / Direct Connect).
- Bedrock model access in-Region (+ a Guardrail in production).
- Named QA reviewers/Qualified Persons for the release gate.

## Deploy (new account, any Region)
```bash
make build-lambdas                                   # vendors deps into each zip
CFN_BUCKET=my-cfn CODE_BUCKET=my-code \
  scripts/deploy.sh 09-manufacturing-batch-review dev portable native
```
This provisions the per-customer VPC, KMS CMK, Cognito SAML→JWT, the dual MCP gateway, the
connector Lambdas (incl. `mes` and `lims` targets), the agent runtime, S3 Object Lock + DynamoDB
append-only audit, and the Step Functions QA gate.

## Demo with no AWS account
```bash
EXTRACT_MODE=demo CONNECTOR_MODE=fixture streamlit run app.py
```
