"""Draft Lambda — calls strands_agent.draft_report for site feasibility report."""
from __future__ import annotations
import json, sys
from typing import Any, Dict
sys.path.insert(0, "/opt/python")
from _shared import audit, ok

try:
    from strands_agent import draft_report
except ImportError:
    from aws_native_reference.site_patient_matching.strands_agent import draft_report  # type: ignore

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    evidence = body.get("evidence", {})
    revision_notes = body.get("revision_notes", "")
    audit_trail = body.get("audit_trail", [])
    revision_count = int(body.get("revision_count", 0))

    draft = draft_report(evidence, revision_notes)

    trail_entry = audit("draft", {
        "study_id": evidence.get("study_id"),
        "revision_count": revision_count,
        "draft_length": len(draft),
    })

    return ok({
        "evidence": evidence,
        "draft": draft,
        "audit_trail": audit_trail + [trail_entry],
        "revision_count": revision_count,
        "revision_notes": revision_notes,
    })
