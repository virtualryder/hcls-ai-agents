#!/usr/bin/env bash
# Golden-path smoke test (fails loudly): start an execution, approve the human gate with a REAL
# bound, separation-of-duties approval, and assert the workflow completed (SUCCEEDED) through the gate.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-02-dev}"
REGION="${AWS_REGION:-us-east-1}"
# Per-run token secret. Reuse the exact secret the deploy step baked into the gateway so the
# locally-minted approval matches GATEWAY_TOKEN_SECRET/APPROVAL_TOKEN_SECRET. Resolution order:
# explicit env > the file deploy.sh persisted (.token_secret.<stack>) > a fresh one (will only
# validate if the stack was deployed with that same secret).
if [ -z "${TOKEN_SECRET:-}" ] && [ -f ".token_secret.$STACK" ]; then
  TOKEN_SECRET="$(cat ".token_secret.$STACK")"
fi
TOKEN_SECRET="${TOKEN_SECRET:-$(python3 -c "import secrets;print(secrets.token_hex(32))")}"
export APPROVAL_TOKEN_SECRET="$TOKEN_SECRET"
export GATEWAY_TOKEN_SECRET="$TOKEN_SECRET"

SM_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" --output text)
[ -n "$SM_ARN" ] || { echo "FAIL: no StateMachineArn output on $STACK"; exit 1; }
echo "State machine: $SM_ARN"

INPUT=$(cat ../../aws-native-reference/02-pharmacovigilance/sample_input.json)
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input "$INPUT" --region "$REGION" --query executionArn --output text)
echo "Started: $EXEC_ARN"

echo "==> waiting for the human gate (waitForTaskToken)…"
TOKEN=""
for i in $(seq 1 90); do   # up to ~180s: the draft step calls Bedrock (real model) and can be slow
  TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
    --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text 2>/dev/null | \
    grep -o '"task_token":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
  [ -n "$TOKEN" ] && break; sleep 2
done
[ -n "$TOKEN" ] || { echo "FAIL: human-gate task token never appeared"; exit 1; }
echo "==> a reviewer mints a BOUND approval (separation of duties) and approves"
APPROVAL=$(python3 mint_approval.py)
aws stepfunctions send-task-success --task-token "$TOKEN" --region "$REGION" --task-output "$APPROVAL"

STATUS="RUNNING"
for i in $(seq 1 30); do
  STATUS=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query status --output text)
  [ "$STATUS" != "RUNNING" ] && break; sleep 2
done
OUT=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query output --output text)
CASE=$(printf '%s' "$OUT" | python3 -c "import sys,json
b=json.load(sys.stdin)
body=b.get('body')
if isinstance(body,str):
    try: body=json.loads(body)
    except Exception: body={}
if not isinstance(body,dict): body={}
print(b.get('case_status') or body.get('case_status',''))" 2>/dev/null || echo "")
echo "status=$STATUS case_status=$CASE"
if [ "$STATUS" = "SUCCEEDED" ] && [ "$CASE" = "SUBMITTED" ]; then
  echo "PASS: governed human gate honored a BOUND approval and the case was SUBMITTED."; exit 0
fi
echo "FAIL: execution status=$STATUS case_status=$CASE (expected SUCCEEDED / SUBMITTED)."; exit 1
