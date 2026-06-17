"""
Finalize Lambda — submit the ICSR to the safety database ONLY after human approval.

Receives the PV Medical Reviewer decision forwarded from the HITL gate:
  review.approved = True  → call submit_report, set case_status = SUBMITTED
  review.approved = False → set case_status = PENDING_REVIEW (no filing)

High-risk write: no code path reaches submit_report without the waitForTaskToken
human gate having fired first (enforced by the Step Functions state machine).
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok, err


def _submit_report(case_state: Dict[str, Any]) -> str:
    """
    Stub for the gateway-authorized safety DB write.
    Production: calls an authorized API with a scoped, reviewer-bound token.
    """
    case_id = case_state.get("case_id", "ICSR-UNKNOWN")
    return f"SUBMITTED-{case_id}"


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    case_state = dict(body)
    audit_trail = case_state.pop("audit_trail", [])

    # The HITL gate result is forwarded into $.review by the ASL ResultPath
    review = case_state.get("review", {})
    approved = bool(review.get("approved"))

    if approved:
        submission_id = _submit_report(case_state)
        case_state["submission_case_id"] = submission_id
        case_state["case_status"] = "SUBMITTED"

        # Set reporting deadline from clock
        clock = case_state.get("reporting_clock_days")
        if clock:
            deadline = (
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=int(clock))
            ).date().isoformat()
            case_state["reporting_deadline"] = deadline
    else:
        case_state["case_status"] = "PENDING_REVIEW"

    case_state["audit_trail"] = list(audit_trail)
    trail_entry = audit(
        "finalize",
        {
            "case_id": case_state.get("case_id"),
            "approved": approved,
            "case_status": case_state["case_status"],
            "submission_id": case_state.get("submission_case_id"),
            "reporting_deadline": case_state.get("reporting_deadline"),
            "human_review_required": True,
        },
    )
    case_state["audit_trail"].append(trail_entry)

    return ok(case_state)
