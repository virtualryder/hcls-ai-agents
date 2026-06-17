"""Assemble: gather structured study facts + source docs into the grounding corpus."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    evidence = dict(state.get("study_data", {}))
    evidence.update({"product": state.get("product"), "indication": state.get("indication"),
                     "source_ref": state.get("section_ref")})
    state["evidence"] = evidence
    state.setdefault("revision_count", 0)
    return ok(audit(state, "Assembled evidence corpus", "assemble"))
