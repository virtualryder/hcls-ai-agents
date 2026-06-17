"""Assemble: retrieve HCP profile and approved documents."""
from __future__ import annotations

from typing import Any, Dict, List

from _shared import audit, ok

_DEMO_HCP = {
    "hcp_id": "HCP-DEMO-001",
    "name": "Dr. Jane Smith",
    "specialty": "Endocrinology",
    "institution": "Metro Diabetes Center",
    "clinical_interests": ["type 2 diabetes", "metabolic syndrome"],
}

_DEMO_DOCS: List[Dict[str, Any]] = [
    {
        "doc_id": "DOC-PI-001",
        "title": "Demo-Drug Prescribing Information",
        "version": "3.0",
        "status": "APPROVED",
        "text": (
            "Demo-Drug is indicated for the treatment of type 2 diabetes mellitus in adults. "
            "In STUDY-301 (n=450), Demo-Drug reduced HbA1c by 1.2 percentage points vs placebo. "
            "Common adverse events: upper respiratory infection (8%), nausea (6%). "
            "Contraindicated in severe renal impairment (eGFR < 30)."
        ),
    },
]


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    state.setdefault("revision_count", 0)

    # Use provided HCP profile or demo fixture
    if not state.get("hcp_profile") or not state.get("hcp_profile", {}).get("name"):
        state["hcp_profile"] = dict(_DEMO_HCP)
        if state.get("hcp_name"):
            state["hcp_profile"]["name"] = state["hcp_name"]

    # Use provided documents or demo fixture
    docs = state.get("approved_documents", [])
    approved = [d for d in docs if isinstance(d, dict) and d.get("status") == "APPROVED"]
    state["approved_documents"] = approved if approved else list(_DEMO_DOCS)

    return ok(audit(state, "Assembled HCP profile and approved documents", "assemble"))
