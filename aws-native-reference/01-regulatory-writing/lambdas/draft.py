"""Draft: invoke the Strands/Bedrock drafter on the assembled evidence."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strands_agent import draft_section
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    out = draft_section(state.get("evidence", {}))
    state["draft"] = out["draft"]
    state["drafted_by"] = out["drafted_by"]
    return ok(audit(state, f"Drafted section ({out['drafted_by']})", "draft"))
