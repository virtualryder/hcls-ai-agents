"""
Assemble: gather regulatory guidance references, feasibility data, and
study parameters into the grounding evidence corpus for the protocol drafter.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)

    # Build grounding evidence corpus for the drafter
    guidance = state.get("guidance_hits", [])
    cohort = state.get("cohort_estimate", {})

    evidence = {
        "indication": state.get("indication"),
        "phase": state.get("phase"),
        "therapeutic_area": state.get("therapeutic_area"),
        "primary_objective": state.get("primary_objective"),
        "target_population": state.get("target_population"),
        "study_design": state.get("study_design"),
        "guidance_count": len(guidance),
        "guidance_refs": [g.get("ref", "") for g in guidance],
        "total_eligible": cohort.get("total_eligible"),
        "sites_with_data": cohort.get("sites_with_data"),
        "phi_note": cohort.get("phi_note", "Aggregate de-identified counts only."),
    }
    state["evidence"] = evidence
    state.setdefault("revision_count", 0)

    return ok(audit(state, "Assembled protocol design evidence corpus", "assemble"))
