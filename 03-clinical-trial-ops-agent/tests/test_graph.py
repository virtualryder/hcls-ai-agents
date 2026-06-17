"""Integration tests: Clinical Trial Ops graph end-to-end in demo mode."""
import os, sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_clinical_trial_ops_graph
from agent.state import RecommendedAction


def _seed(request_id="CLINOPS-TEST-001", study_id="DEMO-STUDY-001",
          subject_data=None, tmf_data=None, enrolled=124, target=200):
    base = {
        "request_id": request_id,
        "study_id": study_id,
        "protocol_id": "PROTO-XR-301",
        "sponsor": "Demo Pharma Inc.",
        "indication": "type 2 diabetes",
        "review_period": "2026-Q1",
        "instructions": "Q1 study health review.",
        "acting_user_claims": {"sub": "u-clinops", "custom:hcls_role": "CLINOPS_LEAD"},
        "study_status": {
            "study_id": study_id,
            "sponsor": "Demo Pharma Inc.",
            "phase": "Phase 3",
            "status": "ACTIVE",
            "enrolled_subjects": enrolled,
            "target_enrollment": target,
            "active_sites": 8,
            "planned_sites": 12,
        },
        "tmf_data": tmf_data or {
            "study_id": study_id,
            "completeness_pct": 87,
            "missing_documents": ["Site Activation Log - Site 04"],
            "last_reviewed": "2026-01-15",
        },
    }
    if subject_data is not None:
        base["subject_data"] = subject_data
    return base


_SUBJECTS_WITH_MISSING = [
    {"subject_id": "001-001", "site_id": "SITE-01", "status": "ACTIVE",
     "visit": "Week 12", "missing_fields": ["Weight"],
     "visits_completed": 5, "visits_expected": 6, "open_queries": 1},
    {"subject_id": "001-002", "site_id": "SITE-01", "status": "ACTIVE",
     "visit": "Week 8",  "missing_fields": [],
     "visits_completed": 5, "visits_expected": 6, "open_queries": 0},
]

_CLEAN_SUBJECTS = [
    {"subject_id": "001-001", "site_id": "SITE-01", "status": "ACTIVE",
     "visit": "Week 12", "missing_fields": [],
     "visits_completed": 6, "visits_expected": 6, "open_queries": 0},
    {"subject_id": "001-002", "site_id": "SITE-01", "status": "COMPLETED",
     "visit": "EOS", "missing_fields": [],
     "visits_completed": 6, "visits_expected": 6, "open_queries": 0},
]

# Truly critical TMF: IRB + Informed Consent + 65% completeness -> CRITICAL
_CRITICAL_TMF = {
    "completeness_pct": 65,
    "missing_documents": [
        "IRB Correspondence - Site 01",
        "Informed Consent Version 2 - Site 02",
        "Investigator Brochure Receipt - Site 03",
    ],
    "last_reviewed": "2025-10-01",
}


def test_graph_runs_without_memory():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    assert out.get("brief_text")
    assert out.get("audit_trail")
    assert out["recommended_action"] in (
        RecommendedAction.APPROVE_BRIEF, RecommendedAction.REVISE, RecommendedAction.ESCALATE,
    )


def test_graph_all_nodes_in_completed_steps():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    steps = out["completed_steps"]
    for expected in ["intake", "pull_study_data", "analyze_tmf", "detect_issues",
                     "draft_queries", "draft_briefing", "quality_check",
                     "human_review_gate", "finalize"]:
        assert expected in steps, f"completed_steps missing: {expected}"


def test_graph_audit_trail_populated():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    nodes_audited = [e["node"] for e in out["audit_trail"]]
    for node in ["intake", "pull_study_data", "analyze_tmf", "detect_issues",
                 "draft_queries", "draft_briefing", "quality_check"]:
        assert node in nodes_audited, f"audit trail missing: {node}"


def test_graph_hitl_gate_node_present():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    assert "human_review_gate" in out["completed_steps"]


def test_graph_tmf_analysis_populated():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    tmf = out.get("tmf_analysis", {})
    assert "inspection_risk" in tmf
    assert "completeness_pct" in tmf


def test_graph_critical_tmf_escalates():
    """65% completeness + IRB/Informed Consent critical docs -> CRITICAL -> ESCALATE."""
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(tmf_data=_CRITICAL_TMF, enrolled=25, target=200))
    # composite: e=30 (25/200=12.5%<50) + t=30 (critical gaps) + q=? + v=? >= 70 -> CRITICAL
    assert out["recommended_action"] == RecommendedAction.ESCALATE


def test_graph_missing_data_flags_detected():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_SUBJECTS_WITH_MISSING))
    assert len(out.get("missing_data_flags", [])) >= 1


def test_graph_no_flags_when_data_clean():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_CLEAN_SUBJECTS))
    assert out.get("missing_data_flags", []) == []


def test_graph_enrollment_metrics_populated():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    em = out.get("enrollment_metrics", {})
    assert "enrolled" in em and "target" in em and "enrollment_pct" in em


def test_graph_risk_score_populated():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    rs = out.get("risk_score", {})
    assert "risk_tier" in rs
    assert rs["risk_tier"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_graph_data_queries_drafted_for_missing_fields():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_SUBJECTS_WITH_MISSING))
    queries = out.get("data_queries", [])
    assert len(queries) >= 1
    assert all(q["status"] == "DRAFT" for q in queries)
    assert all(q["requires_approval"] for q in queries)


def test_graph_query_summary_matches_queries():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_SUBJECTS_WITH_MISSING))
    qs = out.get("query_summary", {})
    assert qs.get("total") == len(out.get("data_queries", []))


def test_graph_brief_is_grounded():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    g = out.get("grounding_report", {})
    assert g.get("grounded"), f"brief should be grounded; report: {g}"


def test_graph_clean_brief_recommends_approval():
    """Seed: HIGH TMF (not CRITICAL) + reasonable enrollment -> APPROVE_BRIEF."""
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_CLEAN_SUBJECTS))
    assert out["recommended_action"] == RecommendedAction.APPROVE_BRIEF


def test_graph_case_status_set():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed())
    assert out.get("case_status") in (
        "REVIEWING", "PENDING_REVIEW", "QUERIES_ISSUED", "FINALIZED"
    )


def test_graph_approve_path_reaches_finalize():
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(subject_data=_CLEAN_SUBJECTS))
    assert "finalize" in out["completed_steps"]


def test_graph_escalate_path_reaches_finalize():
    """ESCALATE still passes through human_review_gate -> finalize."""
    graph = build_clinical_trial_ops_graph(use_memory=False)
    out = graph.invoke(_seed(tmf_data=_CRITICAL_TMF, enrolled=25, target=200))
    assert "finalize" in out["completed_steps"]
    assert out["recommended_action"] == RecommendedAction.ESCALATE
