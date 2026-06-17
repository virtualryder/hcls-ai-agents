"""Draft: invoke the Strands/Bedrock synthesizer on validated cohort evidence."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strands_agent import draft_synthesis
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    cohort_results = state.get("cohort_results", {})
    evidence = state.get("evidence", {})
    out = draft_synthesis(cohort_results, evidence)
    state["synthesis"] = out["synthesis"]
    state["drafted_by"] = out["drafted_by"]
    return ok(audit(state, f"Synthesized evidence ({out['drafted_by']})", "synthesize"))
