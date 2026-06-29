#!/usr/bin/env python3
"""Reviewer STAND-IN for the 05-quality-capa smoke test (the deployed reviewer service is the next delivery step).
Mints a BOUND, separation-of-duties approval token (where a write tool applies) and the review decision."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = "05-quality-capa"
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT))
from hcls_agent_platform.mcp_gateway import approvals  # noqa: E402
raw = json.load(open(os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT, "sample_input.json")))
requestor = (raw.get("acting_user_claims") or {}).get("sub", "staff-1")
approver = os.getenv("REVIEWER_SUB", "reviewer-1")  # separation of duties: differs from requestor
tool, args = "qms.create_capa_draft", {"id": raw.get("case_id") or raw.get("batch_id") or raw.get("review_id") or "DRAFT"}
token = approvals.mint_approval_token(requestor=requestor, agent_id=AGENT, tool=tool, args=args, approver=approver)
out = {"approved": True, "decision": "APPROVE", "reviewer": {"sub": approver, "custom:hcls_role": "QUALIFIED_PERSON"}, "token": token}
print(json.dumps(out))
