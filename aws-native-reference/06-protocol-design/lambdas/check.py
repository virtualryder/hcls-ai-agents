"""Check: deterministic compliance + grounding gate; sets routing + bumps revisions."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    routing = core.route(
        state.get("evidence", {}),
        state.get("draft_protocol", ""),
        state.get("revision_count", 0),
        state=state,
    )
    state["routing"] = routing
    state["compliance_findings"] = routing["compliance"]
    state["grounding_findings"] = routing["grounding"]
    state["regulatory_risks"] = routing.get("regulatory_risks", [])
    if routing["next"] == "Draft":
        state["revision_count"] = state.get("revision_count", 0) + 1
    return ok(audit(state, f"Checks complete -> {routing['action']}", "check"))
