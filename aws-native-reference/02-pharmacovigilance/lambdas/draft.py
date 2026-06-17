"""
Draft Lambda — calls strands_agent.draft_narrative to produce the ICSR narrative.

In EXTRACT_MODE=demo (or when BEDROCK_* env vars are absent) this is fully
deterministic and runs without any AWS credentials.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok
from strands_agent import draft_narrative


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    case_state = dict(body)
    audit_trail = case_state.pop("audit_trail", [])
    revision_count = case_state.get("revision_count", 0)

    out = draft_narrative(case_state)
    case_state["narrative_text"] = out["narrative_text"]
    case_state["drafted_by"] = out["drafted_by"]
    case_state["audit_trail"] = audit_trail

    trail_entry = audit(
        "draft",
        {
            "case_id": case_state.get("case_id"),
            "revision_count": revision_count,
            "drafted_by": out["drafted_by"],
            "narrative_length": len(out["narrative_text"]),
        },
    )
    case_state["audit_trail"].append(trail_entry)

    return ok(case_state)
