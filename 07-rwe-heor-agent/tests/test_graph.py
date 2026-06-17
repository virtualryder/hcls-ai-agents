"""Integration tests: RWE/HEOR graph runs end-to-end in demo mode."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_rwe_heor_graph
from agent.state import RecommendedAction


def _seed_diabetes(request_id="RWE-TEST-E2E"):
    return {
        "request_id": request_id,
        "research_question": (
            "Does SGLT2 inhibitor reduce all-cause hospitalization vs DPP4 inhibitor "
            "in adults with type 2 diabetes over 12 months?"
        ),
        "study_design_type": "Retrospective Cohort",
        "indication": "type 2 diabetes",
        "intervention": "SGLT2 inhibitor",
        "comparator": "DPP4 inhibitor",
        "outcome": "all-cause hospitalization",
        "time_horizon": "12 months",
        "data_source": "US Commercial Claims",
        "instructions": "Synthesize with limitations noted.",
        "acting_user_claims": {"sub": "u-epi", "custom:hcls_role": "EPIDEMIOLOGIST"},
    }


def _seed_psoriasis(request_id="RWE-TEST-PSO"):
    return {
        "request_id": request_id,
        "research_question": (
            "What is treatment persistence at 12 months for IL-17A vs TNF-alpha inhibitor in psoriasis?"
        ),
        "study_design_type": "Retrospective Cohort",
        "indication": "moderate-to-severe psoriasis",
        "intervention": "IL-17A inhibitor",
        "comparator": "TNF-alpha inhibitor",
        "outcome": "treatment persistence at 12 months",
        "time_horizon": "12 months",
        "data_source": "US EHR Network (TriNetX)",
        "instructions": "Note channeling bias.",
        "acting_user_claims": {"sub": "u-epi", "custom:hcls_role": "EPIDEMIOLOGIST"},
    }


def test_graph_runs_without_memory():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes())
    assert out["evidence_synthesis"], "evidence_synthesis must be populated"
    assert out["audit_trail"], "audit_trail must be populated"
    assert out["recommended_action"] in (
        RecommendedAction.APPROVE_SYNTHESIS,
        RecommendedAction.REVISE,
        RecommendedAction.ESCALATE,
    )


def test_graph_populates_all_nodes_in_audit():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-AUDIT"))
    nodes_audited = [e["node"] for e in out["audit_trail"]]
    for expected in [
        "intake", "define_cohort", "run_cohort_query",
        "assess_data_quality", "synthesize_evidence", "grounding_check",
    ]:
        assert expected in nodes_audited, f"audit trail missing node: {expected}"


def test_graph_completed_steps_all_present():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-STEPS"))
    steps = out["completed_steps"]
    for expected in [
        "intake", "define_cohort", "run_cohort_query",
        "assess_data_quality", "synthesize_evidence", "grounding_check",
    ]:
        assert expected in steps, f"completed_steps missing: {expected}"


def test_cohort_definition_populated():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-COHORT"))
    cd = out.get("cohort_definition", {})
    assert cd.get("indication") == "type 2 diabetes"
    assert cd.get("study_design") == "Retrospective Cohort"
    assert "washout_period" in cd


def test_cohort_results_populated():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-RESULTS"))
    assert out.get("cohort_results"), "cohort_results must be populated"
    assert out["cohort_results"].get("n_intervention") == 4821


def test_summary_statistics_populated():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-STATS"))
    stats = out.get("summary_statistics", {})
    assert stats.get("n_intervention") == 4821
    assert stats.get("hazard_ratio") == 0.64


def test_data_quality_assessed():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-QA"))
    qa = out.get("data_quality", {})
    assert "quality_score" in qa
    assert "cohort_balance" in qa


def test_psoriasis_cohort_confounding_flags():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_psoriasis())
    qa = out.get("data_quality", {})
    assert any("biologic" in f or "channeling" in f for f in qa.get("confounding_flags", []))


def test_synthesis_grounded_and_clean():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-GROUND"))
    g = out.get("grounding_report", {})
    assert g.get("grounded"), f"synthesis must be grounded; report: {g}"
    assert out.get("quality_findings", []) == [], (
        f"unexpected quality findings: {out.get('quality_findings')}"
    )


def test_clean_synthesis_recommends_approval():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-APPROVE"))
    assert out["recommended_action"] == RecommendedAction.APPROVE_SYNTHESIS


def test_graph_reaches_human_review_gate():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-GATE"))
    assert "human_review_gate" in out.get("completed_steps", [])


def test_finalize_sets_status():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-FIN"))
    assert out["case_status"] in ("FINALIZED", "PENDING_REVIEW")


def test_audit_trail_has_human_review_required_flag():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_diabetes("RWE-HR"))
    hr_entries = [e for e in out["audit_trail"] if e.get("human_review_required")]
    assert len(hr_entries) >= 1, "at least one audit entry must flag human_review_required"


def test_psoriasis_synthesis_grounded():
    graph = build_rwe_heor_graph(use_memory=False)
    out = graph.invoke(_seed_psoriasis("RWE-PSO-GROUND"))
    g = out.get("grounding_report", {})
    assert g.get("grounded"), f"psoriasis synthesis must be grounded; report: {g}"


def test_graph_second_run_independent():
    graph = build_rwe_heor_graph(use_memory=False)
    out1 = graph.invoke(_seed_diabetes("RWE-INDEP-1"))
    out2 = graph.invoke(_seed_psoriasis("RWE-INDEP-2"))
    assert out1["indication"] == "type 2 diabetes"
    assert out2["indication"] == "moderate-to-severe psoriasis"
