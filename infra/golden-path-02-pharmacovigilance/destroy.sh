#!/usr/bin/env bash
# Tear down the golden-path stack. The audit + pending tables use DeletionPolicy: Retain (PITR) so
# CloudFormation leaves them; for this reproducible golden-path demo we then remove them explicitly so
# a subsequent deploy does not fail EarlyValidation ResourceExistenceCheck on the fixed table names.
# Export any evidence you need (the audit table) BEFORE running this.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-02-dev}"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${STACK#hcls-02-}"; ENVIRONMENT="${ENVIRONMENT:-dev}"

# Stop any executions still paused at the human gate FIRST — a RUNNING execution keeps the state
# machine (and thus the whole stack delete) IN_PROGRESS for a long time.
SM_ARN=$(aws stepfunctions list-state-machines --region "$REGION" \
  --query "stateMachines[?name=='$STACK'].stateMachineArn" --output text 2>/dev/null || true)
if [ -n "$SM_ARN" ] && [ "$SM_ARN" != "None" ]; then
  for E in $(aws stepfunctions list-executions --state-machine-arn "$SM_ARN" --status-filter RUNNING \
      --region "$REGION" --query "executions[*].executionArn" --output text 2>/dev/null); do
    aws stepfunctions stop-execution --execution-arn "$E" --region "$REGION" >/dev/null 2>&1 \
      && echo "stopped running execution $E" || true
  done
fi

sam delete --stack-name "$STACK" --region "$REGION" --no-prompts || true

# Remove the retained tables (fixed names) so re-deploy is clean. Comment this block out to keep audit
# history across re-deploys in a real environment.
for T in "hcls-02-${ENVIRONMENT}-audit" "hcls-02-${ENVIRONMENT}-pending-approvals" "hcls-02-${ENVIRONMENT}-approval-consumption"; do
  aws dynamodb delete-table --table-name "$T" --region "$REGION" >/dev/null 2>&1 \
    && echo "removed retained table $T" || true
done

# Remove Lambda-auto-created CloudWatch log groups (/aws/lambda/hcls-02-<env>-*). Lambda creates these
# on first invocation OUTSIDE CloudFormation, so `sam delete` leaves them behind — delete them for a
# zero-residual teardown.
for LG in $(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/hcls-02-${ENVIRONMENT}-" \
    --region "$REGION" --query "logGroups[].logGroupName" --output text 2>/dev/null); do
  aws logs delete-log-group --log-group-name "$LG" --region "$REGION" >/dev/null 2>&1 \
    && echo "removed lambda log group $LG" || true
done

rm -f ".token_secret.$STACK"
echo "Deleted $STACK, its retained tables, and Lambda log groups; removed local token secret."
