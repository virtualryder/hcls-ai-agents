"""Unit tests for Medical Affairs MSL tools (demo mode, no API key). ~20 tests."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from tools import (
    hcp_profiler,
    content_retriever,
    brief_drafter,
    next_best_action,
    compliance_checker,
)

# ── Shared fixtures ────────────────────────────────────────────────────────────

_HCP_PROFILE = {
    "hcp_id": "HCP-DEMO-001",
    "name": "Dr. Jane Smith",
    "specialty": "Endocrinology",
    "institution": "Metro Diabetes Center",
    "clinical_interests": ["type 2 diabetes", "metabolic syndrome", "cardiovascular risk"],
    "recent_publications": ["Glycemic control in T2D: a 2025 review"],
    "meeting_history": [
        {"date": "2025-10-15", "topic": "Phase 3 data overview", "outcome": "Requested references"},
    ],
}

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
            "(HbA1c reduction 1.2 pp). Cardiovascular safety: no increase in MACE."
        ),
    },
]

_STATE = {
    "hcp_id": "HCP-DEMO-001",
    "hcp_name": "Dr. Jane Smith",
    "topic": "Demo-Drug in type 2 diabetes",
    "meeting_date": "2026-02-15",
    "meeting_purpose": "Scientific exchange on Phase 3 data",
    "hcp_profile": dict(_HCP_PROFILE),
    "approved_documents": list(_APPROVED_DOCS),
    "next_best_actions": {
        "follow_up_actions": [
            "Log interaction in CRM system within the same business day.",
            "Send approved references cited in this brief.",
        ],
        "crm_update_required": True,
        "send_documents": ["Demo-Drug Prescribing Information"],
        "escalation_required": False,
        "escalation_reason": None,
    },
}


# ── HCP profiler ───────────────────────────────────────────────────────────────

def test_hcp_profile_validation_valid():
    v = hcp_profiler.validate_hcp_profile(_HCP_PROFILE)
    assert v["valid"], f"valid profile should pass: {v['issues']}"


def test_hcp_profile_validation_missing_name():
    v = hcp_profiler.validate_hcp_profile({"specialty": "Endocrinology"})
    assert not v["valid"]
    assert any("name" in i for i in v["issues"])


def test_hcp_profile_enrich_adds_tier():
    enriched = hcp_profiler.enrich_hcp_profile(_HCP_PROFILE, "type 2 diabetes")
    assert "engagement_tier" in enriched
    assert enriched["engagement_tier"]


def test_hcp_profile_enrich_relevant_interests():
    enriched = hcp_profiler.enrich_hcp_profile(_HCP_PROFILE, "type 2 diabetes")
    interests = enriched.get("relevant_interests", [])
    assert isinstance(interests, list)
    assert len(interests) > 0


def test_hcp_profile_enrich_prior_interaction_count():
    enriched = hcp_profiler.enrich_hcp_profile(_HCP_PROFILE, "diabetes")
    assert enriched["prior_interaction_count"] == 1


# ── Content retriever ──────────────────────────────────────────────────────────

def test_content_retriever_approves_approved_docs():
    result = content_retriever.validate_documents(_APPROVED_DOCS)
    assert len(result["approved"]) == 2
    assert len(result["blocked"]) == 0
    assert result["issues"] == []


def test_content_retriever_blocks_draft_doc():
    docs = [{"doc_id": "D1", "title": "Draft PI", "status": "DRAFT", "text": "draft"}]
    result = content_retriever.validate_documents(docs)
    assert len(result["blocked"]) == 1
    assert any("DRAFT" in i for i in result["issues"])


def test_content_retriever_citation_index():
    idx = content_retriever.build_citation_index(_APPROVED_DOCS)
    assert len(idx) == 2
    assert any("DOC-PI-001" in k for k in idx)


# ── Brief drafter ──────────────────────────────────────────────────────────────

def test_demo_brief_is_compliant_and_grounded():
    out = brief_drafter.draft_brief(_STATE)
    assert out["drafted_by"].startswith("demo")
    text = out["brief_text"]
    assert len(text.split()) >= 30
    findings = compliance_checker.compliance_findings(text)
    assert findings == [], f"unexpected compliance findings: {findings}"
    g = compliance_checker.grounding_findings(text, _STATE)
    assert g["grounded"], f"ungrounded: {g}"


def test_demo_brief_contains_hcp_name():
    out = brief_drafter.draft_brief(_STATE)
    assert "Dr. Jane Smith" in out["brief_text"]


def test_demo_brief_contains_compliance_note():
    out = brief_drafter.draft_brief(_STATE)
    text = out["brief_text"].lower()
    assert "compliance" in text or "approver" in text or "on-label" in text


# ── Next best action ───────────────────────────────────────────────────────────

def test_nba_clean_brief_includes_crm_logging():
    enriched = hcp_profiler.enrich_hcp_profile(_HCP_PROFILE, "type 2 diabetes")
    nba = next_best_action.recommend_actions(
        hcp_profile=enriched,
        meeting_purpose="Scientific exchange",
        topic="Demo-Drug in type 2 diabetes",
        approved_docs=_APPROVED_DOCS,
        compliance_findings=[],
    )
    assert nba["crm_update_required"]
    assert any("CRM" in a or "log" in a.lower() for a in nba["follow_up_actions"])


def test_nba_off_label_finding_escalates():
    nba = next_best_action.recommend_actions(
        hcp_profile=_HCP_PROFILE,
        meeting_purpose="Scientific exchange",
        topic="Demo-Drug in type 2 diabetes",
        approved_docs=_APPROVED_DOCS,
        compliance_findings=["prohibited off-label reference detected"],
    )
    assert nba["escalation_required"]
    assert any("ESCALATE" in a for a in nba["follow_up_actions"])


# ── Compliance checker ─────────────────────────────────────────────────────────

def test_compliance_clean_brief():
    out = brief_drafter.draft_brief(_STATE)
    findings = compliance_checker.compliance_findings(out["brief_text"])
    assert findings == [], f"unexpected findings: {findings}"


def test_compliance_flags_off_label():
    bad = "This brief discusses off-label use of Demo-Drug for indication X."
    findings = compliance_checker.compliance_findings(bad)
    assert any("off-label" in f for f in findings)


def test_compliance_flags_promotional():
    bad = "Demo-Drug is best-in-class and a game-changer for all patients with diabetes."
    findings = compliance_checker.compliance_findings(bad)
    assert any("promotional" in f for f in findings)


def test_grounding_flags_invented_number():
    g = compliance_checker.grounding_findings("We enrolled 99999 patients.", _STATE)
    assert not g["grounded"]


def test_grounding_passes_on_state_numbers():
    text = (
        "pre-call brief for meeting with Dr. Jane Smith on 2026-02-15. "
        "hcp background: endocrinology specialist with interests in type 2 diabetes. "
        "approved data per Demo-Drug Prescribing Information. "
        "compliance note: on-label only; medical affairs approver review required."
    )
    g = compliance_checker.grounding_findings(text, _STATE)
    assert g["grounded"], f"state-sourced text should be grounded; report: {g}"
