"""Finalize: after Medical Affairs Approver sign-off, submit brief to MLR review."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    review = state.get("review", {})
    approved = bool(review.get("approved"))
    if approved:
        # Real impl: mlr.submit_for_review via gateway with approver's verified identity
        state["mlr_submission_id"] = "MLR-" + str(state.get("request_id", "PENDING"))
        state["case_status"] = "SUBMITTED_MLR"
    else:
        state["case_status"] = "PENDING_REVIEW"
    return ok(audit(state, f"Finalize MLR submission (approved={approved})", "finalize"))
