"""Check Lambda — compliance, grounding, fairness, and routing via core.py."""
from __future__ import annotations
import json, sys
from typing import Any, Dict
sys.path.insert(0, "/opt/python")
from _shared import audit, ok

try:
    import core
except ImportError:
    from aws_native_reference import site_patient_matching as core  # type: ignore

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    evidence = body.get("evidence", {})
    draft = body.get("draft", "")
    audit_trail = body.get("audit_trail", [])
    revision_count = int(body.get("revision_count", 0))
    revision_notes = body.get("revision_notes", "")

    # Compute fairness flags and add to evidence for routing context
    site_counts = evidence.get("cohort_results", {}).get("site_counts", [])
    flags = core.fairness_flags(site_counts)
    score = core.feasibility_score(
        total_eligible=int(evidence.get("cohort_results", {}).get("total_eligible", 0)),
        target_enrollment=int(evidence.get("target_enrollment", 1)),
        n_sites=len(site_counts),
        n_equity_flags=len([f for f in flags if f["severity"] == "CRITICAL"]),
    )
    evidence = {**evidence, "fairness_flags": flags, "feasibility_score": score}

    routing = core.route(evidence, draft, revision_count)

    trail_entry = audit("check", {
        "study_id": evidence.get("study_id"),
        "action": routing["action"],
        "compliance_issues": len(routing.get("compliance", [])),
        "grounding_issues": len(routing.get("grounding", [])),
        "fairness_flags": len(flags),
        "feasibility_tier": score["tier"],
    })

    return ok({
        "evidence": evidence,
        "draft": draft,
        "routing": routing,
        "audit_trail": audit_trail + [trail_entry],
        "revision_count": revision_count,
        "revision_notes": revision_notes,
    })
