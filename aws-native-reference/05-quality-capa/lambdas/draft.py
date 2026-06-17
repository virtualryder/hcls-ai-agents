"""Draft: invoke the Strands/Bedrock drafter on the assembled quality event evidence."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strands_agent import draft_capa_plan
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    out = draft_capa_plan(state.get("evidence", {}))
    state["capa_plan"] = out["capa_plan"]
    state["drafted_by"] = out["drafted_by"]
    return ok(audit(state, f"Drafted CAPA plan ({out['drafted_by']})", "draft"))
