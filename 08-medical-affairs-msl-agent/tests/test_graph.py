"""Integration tests: Medical Affairs MSL graph runs end-to-end in demo mode."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_medical_affairs_msl_graph
from agent.state import RecommendedAction

_APPROVED_DOCS = [
    {
        "doc_id": "DOC-PI-001",
        "title": "Demo-Drug Prescribing Information",
        "version": "3.0",
        "status": "APPROVED",
        "text": (
            "Demo-Drug is indicated for the treatment of type 2 diabetes mellitus in adults. "
            "In STUDY-301 (n=450), Demo-Drug reduced HbA1c by 1.2 percentage points vs placebo. "
            "Common adverse events: upper respiratory infection (8%), nausea (6%). "
            "Contraindicated in severe renal impairment (eGFR < 30)."
        ),
    },
    {
        "doc_id": "DOC-CSR-001",
        "title": "STUDY-301 Clinical Study Report Summary",
        "version": "1.0",
        "status": "APPROVED",
        "text": (
            "Phase 3 STUDY-301: 450 subjects, 52 weeks. Primary endpoint met "
            "(HbA1c reduction 1.2 pp). On-label indication: T2D management in adults."
        ),
    },
]

_HCP_PROFILE = {
    "hcp_id": "HCP-DEMO-001",
    "name": "Dr. Jane Smith",
    "specialty": "Endocrinology",
    "institution": "Metro Diabetes Center",
    "clinical_interests": ["type 2 diabetes", "metabolic syndrome"],
    "meeting_history": [
        {"date": "2025-10-15", "topic": "Phase 3 data overview", "outcome": "Requested references"},
    ],
}


def _seed(request_id="MSL-TEST-001", hcp_name="Dr. Jane Smith"):
    return {
        "request_id": request_id,
        "hcp_id": "HCP-DEMO-001",
        "hcp_name": hcp_name,
        "topic": "Demo-Drug in type 2 diabetes",
        "meeting_date": "2026-02-15",
        "meeting_purpose": "Scientific exchange on Phase 3 data",
        "instructions": "Focus on primary endpoint and cardiovascular safety.",
        "acting_user_claims": {"sub": "u-msl", "custom:hcls_role": "MSL"},
        "hcp_profile": dict(_HCP_PROFILE),
        "approved_documents": list(_APPROVED_DOCS),
    }


# ── End-to-end graph runs ──────────────────────────────────────────────────────

def test_graph_runs_without_memory():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed())
    assert out.get("brief_text"), "brief_text must be populated"
    assert out["audit_trail"], "audit_trail must be populated"
    assert out["recommended_action"] in (
        RecommendedAction.APPROVE_BRIEF,
        RecommendedAction.REVISE,
        RecommendedAction.ESCALATE,
    )


def test_graph_populates_all_nodes_in_audit():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-AUDIT"))
    nodes_audited = [e["node"] for e in out["audit_trail"]]
    for expected in [
        "intake", "pull_hcp_and_content", "enrich_and_validate",
        "draft_brief", "compliance_check",
    ]:
        assert expected in nodes_audited, f"audit trail missing node: {expected}"


def test_graph_completed_steps_all_present():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-STEPS"))
    steps = out["completed_steps"]
    for expected in [
        "intake", "pull_hcp_and_content", "enrich_and_validate",
        "draft_brief", "compliance_check",
    ]:
        assert expected in steps, f"completed_steps missing: {expected}"


# ── HCP enrichment ─────────────────────────────────────────────────────────────

def test_graph_enriches_hcp_profile():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-ENRICH"))
    prof = out.get("hcp_profile", {})
    assert "engagement_tier" in prof, "profile must be enriched with engagement_tier"
    assert prof.get("prior_interaction_count", -1) >= 0


def test_graph_hcp_profile_valid():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-VALID"))
    assert out.get("hcp_profile_valid"), f"profile should be valid; issues: {out.get('hcp_profile_issues')}"


# ── Document validation ────────────────────────────────────────────────────────

def test_graph_document_validation_runs():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-DOCVAL"))
    dv = out.get("document_validation", {})
    assert "approved" in dv
    assert len(dv["approved"]) == 2
    assert len(dv.get("blocked", [])) == 0


def test_graph_citation_index_built():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-CIT"))
    idx = out.get("citation_index", {})
    assert len(idx) >= 1


# ── Compliance gate ────────────────────────────────────────────────────────────

def test_clean_brief_recommends_approval():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-APPROVE"))
    assert out["recommended_action"] == RecommendedAction.APPROVE_BRIEF


def test_clean_brief_no_compliance_findings():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-CLEAN"))
    assert out.get("compliance_findings", []) == [], (
        f"unexpected findings: {out.get('compliance_findings')}"
    )


def test_clean_brief_is_grounded():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-GROUND"))
    g = out.get("grounding_report", {})
    assert g.get("grounded"), f"brief must be grounded; report: {g}"


# ── HITL gate ─────────────────────────────────────────────────────────────────

def test_graph_reaches_human_review_gate():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-GATE"))
    assert "human_review_gate" in out.get("completed_steps", [])


def test_audit_trail_has_human_review_required():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-HR"))
    hr_entries = [e for e in out["audit_trail"] if e.get("human_review_required")]
    assert len(hr_entries) >= 1


def test_finalize_sets_case_status():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-FIN"))
    assert out["case_status"] in ("SUBMITTED_MLR", "PENDING_REVIEW")


# ── Off-label escalation (injected post-draft) ────────────────────────────────

def test_off_label_text_triggers_escalation():
    """Inject off-label text into state to test compliance detection."""
    from tools.compliance_checker import compliance_findings
    bad_text = "This brief discusses off-label use of Demo-Drug for pediatric indication X."
    findings = compliance_findings(bad_text)
    assert any("off-label" in f for f in findings), (
        "off-label text must trigger compliance finding"
    )


def test_next_best_actions_populated():
    graph = build_medical_affairs_msl_graph(use_memory=False)
    out = graph.invoke(_seed("MSL-NBA"))
    nba = out.get("next_best_actions", {})
    assert nba.get("crm_update_required"), "CRM update must be flagged"
    assert len(nba.get("follow_up_actions", [])) >= 1
