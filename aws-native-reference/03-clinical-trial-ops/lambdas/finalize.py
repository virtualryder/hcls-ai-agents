"""
Finalize Lambda — records the human decision, seals the audit trail,
and returns the final study health briefing payload.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from _shared import audit, ok, err


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    evidence = body.get("evidence", {})
    routing = body.get("routing", {})
    draft = body.get("draft", "")
    audit_trail = body.get("audit_trail", [])
    human_decision = body.get("human_decision", body.get("decision", "APPROVE_BRIEF"))

    study_id = evidence.get("study_id", "UNKNOWN")

    if human_decision not in {"APPROVE_BRIEF", "REVISE", "ESCALATE"}:
        return err(400, f"invalid human_decision: {human_decision!r}")

    status = (
        "APPROVED" if human_decision == "APPROVE_BRIEF"
        else "ESCALATED" if human_decision == "ESCALATE"
        else "RETURNED_FOR_REVISION"
    )

    trail_entry = audit(
        "finalize",
        {
            "study_id": study_id,
            "human_decision": human_decision,
            "status": status,
            "risk_tier": evidence.get("risk_score", {}).get("risk_tier"),
        },
    )

    return ok(
        {
            "study_id": study_id,
            "status": status,
            "human_decision": human_decision,
            "brief": draft,
            "evidence": evidence,
            "routing": routing,
            "audit_trail": audit_trail + [trail_entry],
        }
    )
