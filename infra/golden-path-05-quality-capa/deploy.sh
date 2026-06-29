#!/usr/bin/env bash
# Golden path: build + deploy the fully wired 05 Quality / CAPA & Complaints agent.
# Prereqs: AWS SAM CLI, credentials for the target account, Bedrock model access enabled.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-05-dev}"
REGION="${AWS_REGION:-us-east-1}"
echo "==> stage shared layer"
bash prepare_layer.sh
echo "==> sam build"
sam build
echo "==> sam deploy (stack: $STACK, region: $REGION)"
sam deploy --stack-name "$STACK" --region "$REGION" \
  --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset \
  --parameter-overrides "Environment=dev ConnectorMode=fixture"
echo "==> outputs"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
