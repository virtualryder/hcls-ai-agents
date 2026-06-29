#!/usr/bin/env bash
#
# deploy.sh — one command to stage templates + code to S3 and deploy the HCLS
# quickstart stack into a NEW customer AWS account. Idempotent: re-run to update.
#
# Prereqs: AWS CLI v2 configured (aws sts get-caller-identity works), Bedrock
# model access granted in this region, and scripts/build_lambdas.sh already run.
#
# Usage:
#   CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket \
#     scripts/deploy.sh <AgentId> [Environment] [GatewayMode] [DeployMode]
#
# Example (new account, portable gateway, native agent, dev):
#   CFN_BUCKET=acme-hcls-cfn CODE_BUCKET=acme-hcls-code \
#     scripts/deploy.sh 02-pharmacovigilance dev portable native
#
set -euo pipefail

AGENT_ID="${1:?AgentId required, e.g. 02-pharmacovigilance}"
ENVIRONMENT="${2:-dev}"
GATEWAY_MODE="${3:-portable}"      # portable | agentcore
DEPLOY_MODE="${4:-native}"         # native   | container
CONNECTOR_MODE="${CONNECTOR_MODE:-fixture}"
IDP_METADATA_URL="${IDP_METADATA_URL:-}"
CALLBACK_URL="${CALLBACK_URL:-https://localhost/callback}"
USER_POOL_DOMAIN_PREFIX="${USER_POOL_DOMAIN_PREFIX:-}"
CONTAINER_IMAGE_URI="${CONTAINER_IMAGE_URI:-}"
AGENT_MODULE="${AGENT_MODULE:-agent.graph:build_graph}"

# F8 — container mode requires a built image. Refuse early with a clear error
# rather than deploying an ECS service with no image (which would fail at runtime
# behind the internal ALB health check). The SAM golden path is the CANONICAL
# pilot path; this container path is the scale-out reference (see README).
if [[ "$DEPLOY_MODE" == "container" && -z "$CONTAINER_IMAGE_URI" ]]; then
  echo "ERROR: DEPLOY_MODE=container requires CONTAINER_IMAGE_URI (the ARM64 ECR image URI)." >&2
  echo "       Build & push it first (docs/DEPLOYMENT-HANDBOOK.md 4.3), then re-run with:" >&2
  echo "       CONTAINER_IMAGE_URI=<acct>.dkr.ecr.<region>.amazonaws.com/hcls-<agent>:latest \\" >&2
  echo "         CFN_BUCKET=... CODE_BUCKET=... scripts/deploy.sh $AGENT_ID $ENVIRONMENT $GATEWAY_MODE container" >&2
  exit 2
fi

: "${CFN_BUCKET:?set CFN_BUCKET (S3 bucket for CloudFormation templates)}"
: "${CODE_BUCKET:?set CODE_BUCKET (S3 bucket for lambda/connector zips)}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="$(aws configure get region || echo us-east-1)"
STACK="hcls-${ENVIRONMENT}-${AGENT_ID}"

echo "==> account: $(aws sts get-caller-identity --query Account --output text)  region: $REGION"
echo "==> stack:   $STACK  (gateway=$GATEWAY_MODE  deploy=$DEPLOY_MODE  connectors=$CONNECTOR_MODE)"

# 1. Ensure buckets exist
for b in "$CFN_BUCKET" "$CODE_BUCKET"; do
  aws s3 ls "s3://$b" >/dev/null 2>&1 || aws s3 mb "s3://$b" --region "$REGION"
done

# 2. Stage component templates
echo "==> staging CloudFormation templates -> s3://$CFN_BUCKET/hcls/"
aws s3 cp "$REPO_ROOT/infra/cloudformation/" "s3://$CFN_BUCKET/hcls/" \
  --recursive --exclude "*" --include "*.yaml"

# 3. Stage code (built by scripts/build_lambdas.sh)
CONNECTOR_ZIP="$REPO_ROOT/aws-native-reference/_shared/connector/build/connector.zip"
LAMBDA_ZIP="$REPO_ROOT/aws-native-reference/$AGENT_ID/build/lambdas.zip"
[[ -f "$CONNECTOR_ZIP" ]] || { echo "ERROR: $CONNECTOR_ZIP missing — run scripts/build_lambdas.sh"; exit 1; }
echo "==> staging code -> s3://$CODE_BUCKET/"
aws s3 cp "$CONNECTOR_ZIP" "s3://$CODE_BUCKET/connector.zip"
if [[ "$DEPLOY_MODE" == "native" ]]; then
  [[ -f "$LAMBDA_ZIP" ]] || { echo "ERROR: $LAMBDA_ZIP missing — run scripts/build_lambdas.sh $AGENT_ID"; exit 1; }
  aws s3 cp "$LAMBDA_ZIP" "s3://$CODE_BUCKET/$AGENT_ID/lambdas.zip"
fi

# 4. Deploy the master stack
echo "==> deploying $STACK ..."
aws cloudformation deploy \
  --template-file "$REPO_ROOT/infra/cloudformation/quickstart.yaml" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION" \
  --parameter-overrides \
      Environment="$ENVIRONMENT" \
      AgentId="$AGENT_ID" \
      DeployMode="$DEPLOY_MODE" \
      GatewayMode="$GATEWAY_MODE" \
      ConnectorMode="$CONNECTOR_MODE" \
      TemplateBaseUrl="https://$CFN_BUCKET.s3.amazonaws.com/hcls" \
      LambdaCodeBucket="$CODE_BUCKET" \
      LambdaCodeKey="$AGENT_ID/lambdas.zip" \
      ConnectorCodeKey="connector.zip" \
      IdpMetadataUrl="$IDP_METADATA_URL" \
      CallbackUrl="$CALLBACK_URL" \
      UserPoolDomainPrefix="$USER_POOL_DOMAIN_PREFIX" \
      ContainerImageUri="$CONTAINER_IMAGE_URI" \
      AgentModule="$AGENT_MODULE"

echo "==> outputs:"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
echo "==> done. Next: docs/DEPLOY-QUICKSTART.md §6 (smoke test + human gate)."
