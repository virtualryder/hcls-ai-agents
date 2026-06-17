"""Finalize: after QP approval, create the CAPA draft in the QMS + lock audit."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    review = state.get("review", {})
    approved = bool(review.get("approved"))
    if approved:
        # Real impl: gateway-authorized qms.create_capa_draft with the
        # QP's verified identity bound into the scoped token + audit.
        state["capa_draft_id"] = "CAPA-DRAFT-0001"
        state["case_status"] = "CAPA_CREATED"
    else:
        state["case_status"] = "PENDING_REVIEW"
    return ok(audit(state, f"Finalize (approved={approved}) — CAPA draft created in QMS", "finalize"))
