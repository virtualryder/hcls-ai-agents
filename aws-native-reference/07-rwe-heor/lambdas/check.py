"""Check: deterministic grounding + compliance gate; sets routing + bumps revisions."""
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
        state.get("cohort_results", {}),
        state.get("synthesis", ""),
        state.get("revision_count", 0),
    )
    state["routing"] = routing
    state["compliance_findings"] = routing["compliance"]
    state["grounding_findings"] = routing["grounding"]
    if routing["next"] == "Synthesize":
        state["revision_count"] = state.get("revision_count", 0) + 1
    return ok(audit(state, f"Checks complete -> {routing['action']}", "check"))
