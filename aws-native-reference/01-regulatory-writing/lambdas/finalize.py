"""Finalize: after human approval, create the RIM submission draft + lock audit."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    review = state.get("review", {})
    approved = bool(review.get("approved"))
    if approved:
        # Real impl: gateway-authorized rim.create_submission_draft with the
        # approver's verified identity bound into the scoped token + audit.
        state["submission_draft_id"] = "SUBM-DRAFT-0001"
        state["case_status"] = "SUBMITTED_DRAFT"
    else:
        state["case_status"] = "PENDING_REVIEW"
    return ok(audit(state, f"Finalize (approved={approved})", "finalize"))
