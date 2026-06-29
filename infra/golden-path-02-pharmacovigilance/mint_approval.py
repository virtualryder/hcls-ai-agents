#!/usr/bin/env python3
"""Reviewer STAND-IN for the 02 smoke test (the deployed reviewer service is the next delivery step).

Mints a BOUND, separation-of-duties approval token for the *consequential* submit and emits the
review decision the native finalize reads (key: ``approval_token``). The token is bound to:
  requestor (the processing subject) ≠ approver (the reviewer)  → separation of duties
  agent_id = 02-pharmacovigilance, tool = safety.submit_report  → cannot be retargeted
  args     = {"case_id": ...}                                   → stable, tamper-evident
and is single-use (jti). finalize verifies all of this before the submit (STRICT_APPROVAL=1)."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = "02-pharmacovigilance"
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
from hcls_agent_platform.mcp_gateway import approvals  # noqa: E402

raw = json.load(open(os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT, "sample_input.json")))
requestor = raw.get("requestor") or (raw.get("acting_user_claims") or {}).get("sub", "pv-agent-02")
approver = os.getenv("REVIEWER_SUB", "pv-physician-1")  # separation of duties: differs from requestor
tool = "safety.submit_report"                            # the human authorizes the consequential commit
args = {"case_id": raw.get("case_id", "ICSR-DRAFT")}     # stable binding (matches finalize)
token = approvals.mint_approval_token(requestor=requestor, agent_id=AGENT, tool=tool, args=args, approver=approver)
print(json.dumps({
    "approved": True,
    "reviewer": {"sub": approver, "custom:hcls_role": "PV_MEDICAL_REVIEWER"},
    "approval_token": token,
}))
