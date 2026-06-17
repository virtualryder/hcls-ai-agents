"""
Draft Lambda — calls strands_agent.draft_briefing to produce the
study health briefing string.  In demo mode (EXTRACT_MODE=demo or
no ANTHROPIC_API_KEY) this is deterministic.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict

# Allow imports from parent dir when running tests
sys.path.insert(0, "/opt/python")

from _shared import audit, ok

# strands_agent lives in the parent package dir at deploy time
try:
    from strands_agent import draft_briefing
except ImportError:  # pragma: no cover
    from aws_native_reference.clinical_trial_ops.strands_agent import draft_briefing  # type: ignore


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    evidence = body.get("evidence", {})
    revision_notes = body.get("revision_notes", "")
    audit_trail = body.get("audit_trail", [])
    revision_count = body.get("revision_count", 0)

    draft = draft_briefing(evidence, revision_notes)

    trail_entry = audit(
        "draft",
        {
            "study_id": evidence.get("study_id"),
            "revision_count": revision_count,
            "draft_length": len(draft),
        },
    )

    return ok(
        {
            "evidence": evidence,
            "draft": draft,
            "audit_trail": audit_trail + [trail_entry],
            "revision_count": revision_count,
            "revision_notes": revision_notes,
        }
    )
