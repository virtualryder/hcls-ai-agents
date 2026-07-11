#!/usr/bin/env bash
# Golden path: build + deploy the fully wired 07 Real-World Evidence / HEOR agent.
# Prereqs: AWS SAM CLI, credentials for the target account, Bedrock model access enabled.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-07-dev}"
REGION="${AWS_REGION:-us-east-1}"
echo "==> stage shared layer"
bash prepare_layer.sh
echo "==> sam build"
sam build
echo "==> generate a strong per-deploy token secret (never committed)"
TOKEN_SECRET=$(python3 -c "import secrets;print(secrets.token_hex(32))")
export APPROVAL_TOKEN_SECRET="$TOKEN_SECRET"
export GATEWAY_TOKEN_SECRET="$TOKEN_SECRET"
echo "==> sam deploy (stack: $STACK, region: $REGION)"
sam deploy --stack-name "$STACK" --region "$REGION" \
  --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset \
  --parameter-overrides "Environment=dev ConnectorMode=fixture TokenSecret=$TOKEN_SECRET"
echo "==> outputs"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
