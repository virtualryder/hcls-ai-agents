"""Assemble: build grounding corpus from cohort query results and context."""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok

# Demo de-identified cohort results keyed by (intervention, comparator)
_DEMO_COHORTS = {
    ("SGLT2 inhibitor", "DPP4 inhibitor"): {
        "query_id": "RWE-NATIVE-001",
        "n_intervention": 4821,
        "n_comparator": 4756,
        "median_follow_up_months": 14,
        "outcome_rate_intervention": "12.4%",
        "outcome_rate_comparator": "18.7%",
        "hazard_ratio": 0.64,
        "ci_lower": 0.52,
        "ci_upper": 0.79,
        "p_value": "<0.001",
        "data_completeness_pct": 94,
        "phi_note": "Aggregate de-identified per 45 CFR 164.514.",
    },
}


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)
    state.setdefault("revision_count", 0)

    # Build grounding corpus from input evidence
    evidence: Dict[str, Any] = {
        "indication": state.get("indication", ""),
        "intervention": state.get("intervention", ""),
        "comparator": state.get("comparator", ""),
        "outcome": state.get("outcome", ""),
        "time_horizon": state.get("time_horizon", ""),
        "data_source": state.get("data_source", ""),
        "study_design": state.get("study_design_type", "Retrospective Cohort"),
    }

    # Use provided cohort_results or pull from demo fixture
    if not state.get("cohort_results"):
        key = (state.get("intervention", ""), state.get("comparator", ""))
        state["cohort_results"] = _DEMO_COHORTS.get(key, {
            "query_id": "RWE-NATIVE-DEFAULT",
            "n_intervention": 2500,
            "n_comparator": 2500,
            "median_follow_up_months": 12,
            "outcome_rate_intervention": "15.0%",
            "outcome_rate_comparator": "20.0%",
            "hazard_ratio": 0.75,
            "p_value": "0.003",
            "data_completeness_pct": 90,
            "phi_note": "Aggregate de-identified.",
        })

    evidence["cohort_results"] = state["cohort_results"]
    state["evidence"] = evidence

    return ok(audit(state, "Assembled cohort evidence corpus", "assemble"))
