"""Draft: invoke the Strands/Bedrock drafter to produce the MSL pre-call brief."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strands_agent import draft_brief
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    out = draft_brief(
        hcp_profile=state.get("hcp_profile", {}),
        approved_docs=state.get("approved_documents", []),
        topic=state.get("topic", ""),
        meeting_date=state.get("meeting_date", ""),
        meeting_purpose=state.get("meeting_purpose", ""),
    )
    state["brief"] = out["brief"]
    state["drafted_by"] = out["drafted_by"]
    return ok(audit(state, f"Drafted MSL brief ({out['drafted_by']})", "draft"))
