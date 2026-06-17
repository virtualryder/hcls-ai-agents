"""Finalize: after reviewer approval, package protocol sections for IND/CTA submission."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    review = state.get("review", {})
    approved = bool(review.get("approved"))
    if approved:
        # Real impl: gateway-authorized rim.create_submission_draft with the
        # reviewer's verified identity bound into the scoped token + audit.
        state["protocol_draft_id"] = "PROTO-DRAFT-0001"
        state["case_status"] = "FINALIZED"
    else:
        state["case_status"] = "PENDING_REVIEW"
    return ok(audit(
        state,
        f"Finalize (approved={approved}) — protocol sections packaged for IND/CTA",
        "finalize",
    ))
