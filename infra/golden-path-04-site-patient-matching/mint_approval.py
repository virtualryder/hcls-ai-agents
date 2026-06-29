#!/usr/bin/env python3
"""Reviewer STAND-IN for the 04-site-patient-matching smoke test (the deployed reviewer service is the next delivery step).
Mints a BOUND, separation-of-duties approval token (where a write tool applies) and the review decision."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = "04-site-patient-matching"
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT))
from hcls_agent_platform.mcp_gateway import approvals  # noqa: E402
raw = json.load(open(os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT, "sample_input.json")))
requestor = (raw.get("acting_user_claims") or {}).get("sub", "staff-1")
approver = os.getenv("REVIEWER_SUB", "reviewer-1")  # separation of duties: differs from requestor
out = {"approved": True, "decision": "APPROVE", "reviewer": {"sub": approver, "custom:hcls_role": "CLINOPS_LEAD"}}  # read/draft-only: no bound write tool
print(json.dumps(out))
