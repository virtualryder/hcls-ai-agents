"""
Deployed reviewer service (round-2 #2) — the authenticated human-approval API.

Replaces the smoke-test `mint_approval.py` stand-in with a real, IdP-authenticated
endpoint. A federated reviewer (Okta/Entra → Cognito JWT) calls POST /approvals/{approval_id}
with a decision. The service:

  1. Reads the reviewer identity + role from the VERIFIED authorizer claims (never the body).
  2. Authorizes the role (must be entitled to approve this action).
  3. Looks up the pending approval (task token + binding) from the review table.
  4. On APPROVE: mints a BOUND approval token SERVER-SIDE (approver = reviewer sub;
     separation of duties enforced) and resumes Step Functions via SendTaskSuccess.
     On REJECT: SendTaskFailure.

The reviewer never holds the signing key and cannot self-approve. The minted token is
attributable (approver = authenticated sub), single-use, args-bound, and time-limited —
the e-signature semantics Part 11 expects. The pure core below is unit-tested; the AWS
glue (DynamoDB lookup, Step Functions callback) is thin and marked for live validation.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from hcls_agent_platform.mcp_gateway import approvals

DEFAULT_APPROVER_ROLES = {
    "PV_MEDICAL_REVIEWER", "QUALIFIED_PERSON", "QA_RELEASE",
    "REGULATORY_APPROVER", "MEDICAL_AFFAIRS_APPROVER", "CLINOPS_LEAD",
}


class ReviewUnauthorized(Exception):
    """The caller is not authenticated or not entitled to approve this action."""


def _claims(event: Dict[str, Any]) -> Dict[str, Any]:
    rc = event.get("requestContext") or {}
    claims = (rc.get("authorizer") or {}).get("jwt", {}).get("claims")
    if isinstance(claims, dict) and claims:
        return claims
    if os.getenv("HCLS_LOCAL_TEST") == "1":  # tests only
        return event.get("identity", {}) or {}
    return {}


def build_review_decision(claims: Dict[str, Any], pending: Dict[str, Any], decision: str,
                          *, allowed_roles: Optional[set] = None) -> Dict[str, Any]:
    """Pure core: authorize the reviewer and produce the Step Functions task output.

    `pending` is the stored review record (carries the approval_binding the agent intends).
    Returns {"task_token", "output"} where output is the SendTaskSuccess body, or raises.
    """
    roles = allowed_roles or DEFAULT_APPROVER_ROLES
    sub = claims.get("sub")
    role = claims.get("custom:hcls_role")
    if not sub:
        raise ReviewUnauthorized("no authenticated reviewer (missing sub)")
    if role not in roles:
        raise ReviewUnauthorized(f"role '{role}' is not entitled to approve")

    binding = pending.get("approval_binding") or {}
    requestor = binding.get("requestor")
    if sub == requestor:
        raise ReviewUnauthorized("self-approval is forbidden (separation of duties)")

    task_token = pending.get("task_token")
    if not task_token:
        raise ReviewUnauthorized("pending review has no task token")

    if decision != "approved":
        return {"task_token": task_token, "approved": False,
                "output": {"approved": False, "reviewer": {"sub": sub, "custom:hcls_role": role}}}

    # Server-side minting: the reviewer authorizes the EXACT bound action.
    token = approvals.mint_approval_token(
        requestor=requestor, approver=sub,
        agent_id=binding.get("agent_id"), tool=binding.get("tool"), args=binding.get("args"))
    return {
        "task_token": task_token, "approved": True,
        "output": {"approved": True,
                   "reviewer": {"sub": sub, "custom:hcls_role": role},
                   "approval_token": token},
    }


# ── AWS glue (thin; validated live) ──────────────────────────────────────────
def _load_pending(approval_id: str) -> Dict[str, Any]:  # pragma: no cover - requires AWS
    import boto3
    table = os.environ["REVIEW_TABLE"]
    resp = boto3.client("dynamodb").get_item(
        TableName=table, Key={"approval_id": {"S": approval_id}}, ConsistentRead=True)
    item = resp.get("Item")
    if not item:
        raise ReviewUnauthorized(f"no pending review {approval_id}")
    return json.loads(item["payload"]["S"])


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:  # pragma: no cover - requires AWS
    import boto3

    claims = _claims(event)
    approval_id = (event.get("pathParameters") or {}).get("approval_id", "")
    body = json.loads(event.get("body") or "{}")
    decision = body.get("decision", "approved")
    try:
        pending = _load_pending(approval_id)
        out = build_review_decision(claims, pending, decision)
    except (ReviewUnauthorized, approvals.ApprovalInvalid) as exc:
        return {"statusCode": 403, "body": json.dumps({"error": str(exc)})}

    sfn = boto3.client("stepfunctions")
    if out["approved"]:
        sfn.send_task_success(taskToken=out["task_token"], output=json.dumps(out["output"]))
    else:
        sfn.send_task_failure(taskToken=out["task_token"], error="ReviewerRejected")
    return {"statusCode": 200, "body": json.dumps({"approved": out["approved"], "approval_id": approval_id})}
