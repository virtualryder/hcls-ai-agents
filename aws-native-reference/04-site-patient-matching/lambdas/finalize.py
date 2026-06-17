"""Finalize Lambda — records human decision and seals audit trail."""
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
    human_decision = body.get("human_decision", body.get("decision", "APPROVE_RANKING"))

    study_id = evidence.get("study_id", "UNKNOWN")

    if human_decision not in {"APPROVE_RANKING", "REVISE", "ESCALATE"}:
        return err(400, f"invalid human_decision: {human_decision!r}")

    status = (
        "APPROVED" if human_decision == "APPROVE_RANKING"
        else "ESCALATED" if human_decision == "ESCALATE"
        else "RETURNED_FOR_REVISION"
    )

    trail_entry = audit("finalize", {
        "study_id": study_id,
        "human_decision": human_decision,
        "status": status,
        "feasibility_tier": evidence.get("feasibility_score", {}).get("tier"),
    })

    return ok({
        "study_id": study_id,
        "status": status,
        "human_decision": human_decision,
        "ranking_report": draft,
        "evidence": evidence,
        "routing": routing,
        "audit_trail": audit_trail + [trail_entry],
    })
