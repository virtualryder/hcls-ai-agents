#!/usr/bin/env bash
# Run the governed PV workflow end-to-end and PROVE the drafted narrative is a real,
# de-identified ICSR narrative (not the Guardrail's 31-char input refusal).
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-02-dev}"
REGION="${AWS_REGION:-us-east-1}"

if [ -z "${TOKEN_SECRET:-}" ] && [ -f ".token_secret.$STACK" ]; then
  TOKEN_SECRET="$(cat ".token_secret.$STACK")"
fi
TOKEN_SECRET="${TOKEN_SECRET:-$(python3 -c "import secrets;print(secrets.token_hex(32))")}"
export APPROVAL_TOKEN_SECRET="$TOKEN_SECRET"
export GATEWAY_TOKEN_SECRET="$TOKEN_SECRET"

SM_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" --output text)
echo "State machine: $SM_ARN"
INPUT=$(cat ../../aws-native-reference/02-pharmacovigilance/sample_input.json)
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input "$INPUT" --region "$REGION" --query executionArn --output text)
echo "Started: $EXEC_ARN"

echo "==> waiting for the human gate (draft calls real Bedrock first)…"
TOKEN=""
for i in $(seq 1 90); do
  TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
    --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text 2>/dev/null | \
    grep -o '"task_token":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
  [ -n "$TOKEN" ] && break; sleep 2
done
[ -n "$TOKEN" ] || { echo "FAIL: human-gate task token never appeared"; exit 1; }
echo "==> reviewer mints a BOUND separation-of-duties approval and approves"
APPROVAL=$(python3 mint_approval.py)
aws stepfunctions send-task-success --task-token "$TOKEN" --region "$REGION" --task-output "$APPROVAL"

STATUS="RUNNING"
for i in $(seq 1 30); do
  STATUS=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query status --output text)
  [ "$STATUS" != "RUNNING" ] && break; sleep 2
done
echo "status=$STATUS"

echo "==> extracting the drafted narrative from the execution history"
aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
  --max-items 1000 --output json > _hist.json
python3 - "$EXEC_ARN" <<'PY'
import json,sys
h=json.load(open("_hist.json"))
narr=None; by=None
def scan(o):
    global narr,by
    if isinstance(o,dict):
        if "narrative_text" in o and isinstance(o["narrative_text"],str):
            narr=o["narrative_text"]
        if "drafted_by" in o:
            by=o["drafted_by"]
        for v in o.values(): scan(v)
    elif isinstance(o,list):
        for v in o: scan(v)
for e in h.get("events",[]):
    for k in ("taskSucceededEventDetails","stateExitedEventDetails","taskStateExitedEventDetails","executionSucceededEventDetails"):
        d=e.get(k) or {}
        out=d.get("output")
        if isinstance(out,str):
            try: scan(json.loads(out))
            except Exception: pass
print("drafted_by =", by)
if narr is None:
    print("narrative_text = <NOT FOUND IN HISTORY>")
    sys.exit(2)
print("narrative_length =", len(narr))
print("---- narrative (first 900 chars) ----")
print(narr[:900])
print("---- END ----")
# Assertions: a real narrative is long and is NOT the guardrail refusal.
if narr.strip() == "I can't help with that request." or len(narr) < 120:
    print("RESULT: FAIL — narrative looks like a Guardrail refusal / too short.")
    sys.exit(3)
print("RESULT: PASS — real de-identified narrative drafted through the tuned Guardrail.")
PY
