from __future__ import annotations
import os, sys
from pathlib import Path
AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"
import pytest
from agent.graph import build_site_patient_matching_graph
from agent.state import RecommendedAction

_COHORT = {
    "query_id": "DEMO-Q-001",
    "total_eligible": 1847,
    "sites_with_data": 6,
    "site_counts": [
        {"site_id": "SITE-NE-01", "region": "Northeast", "eligible_count": 423,
         "demographics": {"pct_female": 52, "pct_hispanic": 18, "pct_black": 14}},
        {"site_id": "SITE-SE-01", "region": "Southeast", "eligible_count": 387,
         "demographics": {"pct_female": 49, "pct_hispanic": 22, "pct_black": 28}},
        {"site_id": "SITE-MW-01", "region": "Midwest", "eligible_count": 312,
         "demographics": {"pct_female": 48, "pct_hispanic": 9, "pct_black": 11}},
        {"site_id": "SITE-W-01", "region": "West", "eligible_count": 298,
         "demographics": {"pct_female": 51, "pct_hispanic": 31, "pct_black": 8}},
        {"site_id": "SITE-SW-01", "region": "Southwest", "eligible_count": 251,
         "demographics": {"pct_female": 47, "pct_hispanic": 38, "pct_black": 7}},
        {"site_id": "SITE-NW-01", "region": "Northwest", "eligible_count": 176,
         "demographics": {"pct_female": 53, "pct_hispanic": 12, "pct_black": 5}},
    ],
    "phi_note": "All counts are aggregate and de-identified per 45 CFR 164.514.",
}


def _seed(**kwargs):
    base = {
        "request_id": "MATCH-TEST-001",
        "study_id": "DEMO-STUDY-001",
        "protocol_id": "PROTO-XR-301",
        "indication": "type 2 diabetes",
        "target_enrollment": 200,
        "instructions": "Identify top sites.",
        "acting_user_claims": {"sub": "u-epi", "custom:hcls_role": "EPIDEMIOLOGIST"},
        "eligibility_criteria": {
            "age_min": 18, "age_max": 75,
            "diagnosis_codes": ["E11", "E11.9"],
            "lab_thresholds": {"HbA1c": 7.5},
            "exclusions": ["eGFR < 30"],
        },
        "cohort_results": _COHORT,
    }
    base.update(kwargs)
    return base


def _run(**kwargs):
    g = build_site_patient_matching_graph(use_memory=False)
    return g.invoke(_seed(**kwargs))


# Basic end-to-end
def test_graph_runs_without_memory():
    out = _run()
    assert out.get("ranking_report"), "ranking_report must be populated"
    assert "fairness_review" in out["completed_steps"]


def test_all_nodes_in_completed_steps():
    out = _run()
    for node in ("intake", "translate_criteria", "run_cohort_query",
                 "estimate_cohorts", "rank_sites", "fairness_review"):
        assert node in out["completed_steps"], f"missing: {node}"


def test_audit_trail_populated():
    out = _run()
    assert len(out["audit_trail"]) >= 6


def test_case_status_pending_review():
    out = _run()
    assert out["case_status"] == "FINALIZED"  # no interrupt in use_memory=False mode


# Eligibility translation
def test_cohort_query_populated():
    out = _run()
    q = out.get("cohort_query", {})
    assert q.get("cdisc_compliant") is True
    assert q.get("translated_fields", 0) > 0


def test_cohort_query_has_age_filters():
    out = _run()
    age_f = [f for f in out["cohort_query"]["filters"] if f["field"] == "age_years"]
    assert len(age_f) == 2


# Cohort estimation
def test_cohort_estimates_populated():
    out = _run()
    est = out.get("cohort_estimates", {})
    assert "total_projected_enrollees" in est
    assert "portfolio_feasible" in est
    assert len(est.get("sites", [])) > 0


def test_cohort_estimates_top_sites():
    out = _run()
    assert len(out["cohort_estimates"].get("top_recommended_sites", [])) > 0


# Site ranking
def test_site_rankings_populated():
    out = _run()
    assert len(out.get("site_rankings", [])) >= 1


def test_site_rankings_have_rank_field():
    out = _run()
    for site in out["site_rankings"]:
        assert "rank" in site


# Fairness flags
def test_fairness_flags_populated():
    out = _run()
    assert isinstance(out.get("fairness_flags"), list)


# Grounding
def test_grounding_report_populated():
    out = _run()
    gr = out.get("grounding_report", {})
    assert "grounded" in gr


def test_grounding_passes_for_demo_report():
    out = _run()
    assert out["grounding_report"]["grounded"], str(out["grounding_report"])


# Disposition
def test_clean_ranking_recommends_approval():
    out = _run()
    assert out["recommended_action"] == RecommendedAction.APPROVE_RANKING


def test_escalate_on_critical_equity_flag():
    # inject a pre-computed state with a CRITICAL fairness flag
    g = build_site_patient_matching_graph(use_memory=False)
    state = _seed()
    state["fairness_flags"] = [{
        "site_id": "SITE-NE-01",
        "demographic": "Black/African American",
        "description": "Site SITE-NE-01 has critical under-representation.",
        "severity": "CRITICAL",
    }]
    state["site_rankings"] = _COHORT["site_counts"]
    state["ranking_report"] = (
        "Site feasibility report for DEMO-STUDY-001 type 2 diabetes. "
        "Target enrollment: 200. Cohort identified 1847 eligible patients across 6 sites. "
        "All data is de-identified aggregate per 45 CFR 164.514. "
        "Top site: SITE-NE-01. Rank 1. Requires human review."
    )
    state["cohort_estimates"] = {"total_projected_enrollees": 500, "portfolio_feasible": True,
                                 "sites": [], "top_recommended_sites": ["SITE-NE-01"]}
    state["revision_count"] = 0
    state["completed_steps"] = [
        "intake", "translate_criteria", "run_cohort_query", "estimate_cohorts", "rank_sites",
    ]
    state["audit_trail"] = []
    from agent.nodes import fairness_review
    out = fairness_review(state)
    assert out["recommended_action"] == RecommendedAction.ESCALATE


# HITL gate
def test_interrupt_before_human_review_gate():
    g = build_site_patient_matching_graph(use_memory=True)
    config = {"configurable": {"thread_id": "test-04-hitl"}}
    result = g.invoke(_seed(), config=config)
    state = g.get_state(config)
    next_nodes = list(state.next)
    assert next_nodes == ["human_review_gate"], f"expected HITL interrupt, got {next_nodes}"


def test_resume_after_hitl_reaches_finalize():
    g = build_site_patient_matching_graph(use_memory=True)
    config = {"configurable": {"thread_id": "test-04-resume"}}
    g.invoke(_seed(), config=config)
    state = g.get_state(config)
    assert state.next == ("human_review_gate",)
    final = g.invoke(None, config=config)
    assert "finalize" in final["completed_steps"]
    assert final["case_status"] == "FINALIZED"


def test_quality_findings_list_present():
    out = _run()
    assert "quality_findings" in out
    assert isinstance(out["quality_findings"], list)
