"""Finalize: after Epidemiologist approval, lock audit trail and publish synthesis."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    review = state.get("review", {})
    approved = bool(review.get("approved"))
    if approved:
        # Real impl: publish to evidence repository / dossier management system
        # with approver's verified identity bound to the scoped token + audit.
        state["evidence_package_id"] = "RWE-PKG-" + str(state.get("request_id", "0001"))
        state["case_status"] = "FINALIZED"
    else:
        state["case_status"] = "PENDING_REVIEW"
    return ok(audit(state, f"Finalize (approved={approved})", "finalize"))
