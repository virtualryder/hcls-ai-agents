"""Resume a waiting 02 execution: mint a bound approval and SendTaskSuccess, then assert.
Usage: python smoke_resume.py <executionArn>   (boto3; avoids CLI JSON quoting issues)"""
import json, os, sys, time, boto3

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "platform_core"))
if not os.environ.get("APPROVAL_TOKEN_SECRET"):
    sys.exit("APPROVAL_TOKEN_SECRET must be set to the strong per-deploy secret used at deploy time "
             "(no committed default). Reuse the value from deploy.sh/smoke_test.sh so the minted "
             "approval matches the deployed GATEWAY_TOKEN_SECRET.")
from hcls_agent_platform.mcp_gateway import approvals

region = os.environ.get("AWS_REGION", "us-east-1")
sfn = boto3.client("stepfunctions", region_name=region)
exec_arn = sys.argv[1]

# 1. find the waiting task token
token = None
hist = sfn.get_execution_history(executionArn=exec_arn, reverseOrder=True, maxResults=30)
for e in hist["events"]:
    if e["type"] == "TaskScheduled":
        params = json.loads(e["taskScheduledEventDetails"]["parameters"])
        token = params.get("Payload", {}).get("task_token")
        if token:
            break
if not token:
    print("NO_TOKEN status=", sfn.describe_execution(executionArn=exec_arn)["status"]); sys.exit(1)

# 2. mint a BOUND approval for the consequential submit (reviewer != requestor)
raw = json.load(open(os.path.join(REPO, "aws-native-reference", "02-pharmacovigilance", "sample_input.json")))
requestor = raw.get("requestor") or (raw.get("acting_user_claims") or {}).get("sub", "pv-agent-02")
approver = "pv-physician-1"
tok = approvals.mint_approval_token(requestor=requestor, approver=approver,
        agent_id="02-pharmacovigilance", tool="safety.submit_report",
        args={"case_id": raw.get("case_id")})
output = {"approved": True, "reviewer": {"sub": approver, "custom:hcls_role": "PV_MEDICAL_REVIEWER"},
          "approval_token": tok}
sfn.send_task_success(taskToken=token, output=json.dumps(output))
print("APPROVED requestor=%s approver=%s" % (requestor, approver))

# 3. poll to completion
d = None
for _ in range(40):
    d = sfn.describe_execution(executionArn=exec_arn)
    if d["status"] != "RUNNING":
        break
    time.sleep(2)
print("FINAL_STATUS", d["status"])
if d.get("output"):
    o = json.loads(d["output"]); body = o.get("body", o)
    if isinstance(body, str): body = json.loads(body)
    print("case_status:", body.get("case_status"))
    print("approval_verified:", body.get("approval_verified"))
    print("approval_reviewer:", body.get("approval_reviewer"))
    print("submission_case_id:", body.get("submission_case_id"))
