"""Check Lambda — deterministic quality + routing gate (core.route)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import audit, ok
import core


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    state = dict(body)
    report = state.get("exception_report", "")
    revisions = int(state.get("revision_count", 0))
    routing = core.route(state, report, revisions)
    state["routing"] = routing
    if routing["action"] == "REVISE":
        state["revision_count"] = revisions + 1
    state.setdefault("audit_trail", []).append(
        audit("check", {"batch_id": state.get("batch_id"), "action": routing["action"],
                        "grounding_issues": len(routing.get("grounding_findings", [])),
                        "missing_elements": len(routing.get("missing_elements", []))}))
    return ok(state)
