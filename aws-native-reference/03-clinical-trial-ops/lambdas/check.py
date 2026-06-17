"""
Check Lambda — runs compliance_findings, grounding_findings, risk scoring,
and TMF risk assessment via core.py, then calls route() to decide
APPROVE_BRIEF / REVISE / ESCALATE.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict

sys.path.insert(0, "/opt/python")

from _shared import audit, ok

try:
    import core
except ImportError:
    from aws_native_reference import clinical_trial_ops as core  # type: ignore


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    evidence = body.get("evidence", {})
    draft = body.get("draft", "")
    audit_trail = body.get("audit_trail", [])
    revision_count = int(body.get("revision_count", 0))
    revision_notes = body.get("revision_notes", "")

    # Run risk scoring so evidence carries it for routing
    tmf_data = evidence.get("tmf_data", {})
    missing_docs = tmf_data.get("missing_documents", [])
    tmf_pct = float(tmf_data.get("completeness_pct", 100))
    t_risk = core.tmf_risk(missing_docs, tmf_pct)
    rs = core.risk_score(
        enrolled=int(evidence.get("enrolled", 0)),
        target=int(evidence.get("target", 1)),
        tmf_pct=tmf_pct,
        tmf_critical=(t_risk == "CRITICAL"),
        query_rate=float(evidence.get("query_rate", 0)),
    )
    evidence = {**evidence, "risk_score": rs, "tmf_risk": t_risk}

    routing = core.route(evidence, draft, revision_count)

    trail_entry = audit(
        "check",
        {
            "study_id": evidence.get("study_id"),
            "action": routing["action"],
            "compliance_issues": len(routing.get("compliance", [])),
            "grounding_issues": len(routing.get("grounding", [])),
            "risk_tier": rs["risk_tier"],
            "tmf_risk": t_risk,
        },
    )

    return ok(
        {
            "evidence": evidence,
            "draft": draft,
            "routing": routing,
            "audit_trail": audit_trail + [trail_entry],
            "revision_count": revision_count,
            "revision_notes": revision_notes,
        }
    )
