"""
Finalize Lambda — submit the ICSR to the safety database ONLY after a *verified*
human approval.

Inputs (from the ASL): the case body is in ``event["body"]`` and the PV Medical
Reviewer's decision is forwarded as a SIBLING in ``event["review"]`` (the HITL gate
uses ``ResultPath: "$.review"``). Finalize must therefore read the review from the
event sibling — NOT from inside the case body (F4b).

Approval integrity (F2): a bare ``approved: true`` boolean is NOT sufficient to
release a regulated ICSR. When a bound approval token is present it is cryptographically
verified (signature, expiry, separation of duties, exact-args binding, single-use) via
the shared ``hcls_agent_platform`` approval primitive — the SAME logic the MCP gateway
enforces. In production (``STRICT_APPROVAL=1``, set by the golden-path template) a valid
bound token is REQUIRED; any tampered, replayed, self-approved, or missing token fails
closed and the case is NOT submitted.

Submission (F1/F6): the consequential ``safety.submit_report`` write is performed through
the governed connector (when ``SAFETY_CONNECTOR_FUNCTION`` is configured), carrying the
verified approval — so the action approved is exactly the action executed, and the
system-of-record response becomes part of the audit record. With no connector configured
(demo/fixture) a deterministic local id is returned.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok, err

# The shared layer bundles hcls_agent_platform; import the bound-approval verifier.
try:  # pragma: no cover - import shape depends on layer/PYTHONPATH
    from hcls_agent_platform.mcp_gateway import approvals as _approvals
except Exception:  # pragma: no cover
    _approvals = None

AGENT_ID = "02-pharmacovigilance"
SUBMIT_TOOL = "safety.submit_report"


def _requestor(case_state: Dict[str, Any]) -> str:
    """The requesting subject the approval must NOT match (separation of duties)."""
    return (case_state.get("requestor")
            or (case_state.get("acting_user_claims") or {}).get("sub")
            or "pv-agent-02")


def _strict() -> bool:
    return os.getenv("STRICT_APPROVAL") == "1"


def _submit_report(case_state: Dict[str, Any], approval: Optional[Dict[str, Any]]) -> str:
    """Governed safety-DB write.

    Production: invokes the governed connector Lambda with the verified approval, so the
    otherwise-withheld ``safety.submit_report`` commit is authorized by the human approval.
    Demo/fixture: returns a deterministic id (no connector configured).
    """
    case_id = case_state.get("case_id", "ICSR-UNKNOWN")
    fn = os.getenv("SAFETY_CONNECTOR_FUNCTION")
    if not fn:
        return f"SUBMITTED-{case_id}"
    import boto3  # pragma: no cover - requires AWS

    resp = boto3.client("lambda").invoke(  # pragma: no cover - requires AWS
        FunctionName=fn,
        Payload=json.dumps({
            "tool": SUBMIT_TOOL,
            "agent_id": AGENT_ID,
            "arguments": {"case_id": case_id, "meddra_pt": case_state.get("meddra_pt", "")},
            "approval": approval,
        }).encode("utf-8"),
    )
    payload = json.loads(resp["Payload"].read() or b"{}")  # pragma: no cover
    if payload.get("decision") != "ALLOW":  # pragma: no cover
        raise RuntimeError(f"connector denied submit: {payload.get('reason')}")
    return str((payload.get("result") or {}).get("submission_id") or f"SUBMITTED-{case_id}")


def _verify_approval(case_state: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, Any]:
    """Return {'approved': bool, 'verified': bool, 'reviewer': str, 'reason': str, 'approval': dict}.

    Enforcement order:
      * bound approval token present  → cryptographically verify (fail closed on any tamper)
      * no token, STRICT_APPROVAL=1   → reject (a bare boolean is not acceptable in prod)
      * no token, non-strict (demo)   → legacy boolean path, flagged UNVERIFIED
    """
    token = review.get("approval_token")
    requestor = _requestor(case_state)
    # Bind to the stable case_id only: meddra_pt is derived mid-pipeline and would
    # drift between gate-time minting and finalize-time verification.
    args = {"case_id": case_state.get("case_id")}

    if token and _approvals is not None:
        try:
            payload = _approvals.verify_approval_token(
                token,
                requestor=requestor,
                agent_id=AGENT_ID,
                tool=SUBMIT_TOOL,
                args=args,
            )
        except Exception as exc:  # ApprovalInvalid or malformed → fail closed
            return {"approved": False, "verified": False, "reviewer": "",
                    "reason": f"approval rejected: {exc}", "approval": None}
        return {"approved": True, "verified": True,
                "reviewer": payload.get("approver", ""), "reason": "bound approval verified",
                "approval": {"token": token, **payload}}

    if _strict():
        return {"approved": False, "verified": False, "reviewer": "",
                "reason": "STRICT_APPROVAL: a verified bound approval token is required", "approval": None}

    # Demo / fixture path: legacy boolean, explicitly marked unverified.
    return {"approved": bool(review.get("approved")), "verified": False,
            "reviewer": review.get("reviewer", "demo-reviewer"),
            "reason": "demo path: unverified boolean approval", "approval": None}


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    # F4b: case body and reviewer decision arrive as SIBLINGS from the ASL.
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    review = event.get("review", {})
    if isinstance(review, str):
        review = json.loads(review)
    # Backward-compat: tolerate a review nested in the body (older callers).
    if not review and isinstance(body, dict):
        review = body.get("review", {})

    case_state = dict(body)
    case_state.pop("review", None)
    audit_trail = case_state.pop("audit_trail", [])

    decision = _verify_approval(case_state, review)
    approved = decision["approved"]

    if approved:
        submission_id = _submit_report(case_state, decision["approval"])
        case_state["submission_case_id"] = submission_id
        case_state["case_status"] = "SUBMITTED"
        clock = case_state.get("reporting_clock_days")
        if clock:
            deadline = (
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=int(clock))
            ).date().isoformat()
            case_state["reporting_deadline"] = deadline
    else:
        # Fail closed: rejected or unverified-in-strict → not submitted.
        case_state["case_status"] = "PENDING_REVIEW"

    case_state["approval_verified"] = decision["verified"]
    case_state["approval_reviewer"] = decision["reviewer"]

    case_state["audit_trail"] = list(audit_trail)
    trail_entry = audit(
        "finalize",
        {
            "case_id": case_state.get("case_id"),
            "approved": approved,
            "approval_verified": decision["verified"],
            "approval_reviewer": decision["reviewer"],
            "approval_reason": decision["reason"],
            "case_status": case_state["case_status"],
            "submission_id": case_state.get("submission_case_id"),
            "reporting_deadline": case_state.get("reporting_deadline"),
            "human_review_required": True,
        },
    )
    case_state["audit_trail"].append(trail_entry)

    return ok(case_state)
