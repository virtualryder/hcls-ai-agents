#!/usr/bin/env python3
"""Reviewer STAND-IN for the 02 smoke test (the deployed reviewer service is the next delivery step).
Mints a BOUND, separation-of-duties approval token AND the review decision the native finalize reads."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = "02-pharmacovigilance"
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT))
from hcls_agent_platform.mcp_gateway import approvals  # noqa: E402

raw = json.load(open(os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT, "sample_input.json")))
requestor = (raw.get("acting_user_claims") or {}).get("sub", "pv-processor-1")
approver = os.getenv("REVIEWER_SUB", "pv-physician-1")  # separation of duties: differs from requestor
# the agent's reversible write the reviewer is authorizing (the irreversible submit is human-only)
tool, args = "safety.write_case_draft", {"case_id": raw.get("case_id", "ICSR-DRAFT")}
token = approvals.mint_approval_token(requestor=requestor, agent_id=AGENT, tool=tool, args=args, approver=approver)
print(json.dumps({"approved": True, "reviewer": {"sub": approver, "custom:hcls_role": "PV_MEDICAL_REVIEWER"},
                  "token": token}))
