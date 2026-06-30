"""Generic golden-path smoke resume: find the gate token, run THIS agent's mint_approval.py,
SendTaskSuccess, poll to completion. Usage: python resume_any.py <execArn> <goldenPathDir>"""
import json, os, subprocess, sys, time, boto3

exec_arn, gp = sys.argv[1], sys.argv[2]
region = os.environ.get("AWS_REGION", "us-east-1")
sfn = boto3.client("stepfunctions", region_name=region)

# 1. gate token (handle task_token / taskToken across agents)
import re
token = None
for e in sfn.get_execution_history(executionArn=exec_arn, reverseOrder=True, maxResults=40)["events"]:
    if e["type"] == "TaskScheduled":
        raw = e["taskScheduledEventDetails"]["parameters"]
        m = re.search(r'"task_?[Tt]oken"\s*:\s*"([^"]+)"', raw)
        if m: token = m.group(1); break
if not token:
    print("NO_TOKEN status=", sfn.describe_execution(executionArn=exec_arn)["status"]); sys.exit(1)

# 2. this agent's reviewer stand-in mints the approval/decision
env = dict(os.environ, APPROVAL_TOKEN_SECRET=os.environ.get("APPROVAL_TOKEN_SECRET", "dev-only-not-for-production"))
out = subprocess.run([sys.executable, "mint_approval.py"], cwd=gp, capture_output=True, text=True, env=env)
approval = out.stdout.strip()
if not approval:
    print("MINT_FAILED", out.stderr[-400:]); sys.exit(1)
sfn.send_task_success(taskToken=token, output=approval)
print("APPROVED")

# 3. poll
d = None
for _ in range(40):
    d = sfn.describe_execution(executionArn=exec_arn)
    if d["status"] != "RUNNING": break
    time.sleep(2)
print("FINAL_STATUS", d["status"])
if d.get("output"):
    o = json.loads(d["output"]); body = o.get("body", o)
    if isinstance(body, str): body = json.loads(body)
    for k in ("case_status", "batch_status", "tmf_status", "status", "match_status", "disposition_id", "submission_case_id"):
        if k in body: print(f"{k}: {body[k]}")
