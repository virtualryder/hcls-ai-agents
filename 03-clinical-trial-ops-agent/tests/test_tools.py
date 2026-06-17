"""Unit tests for Clinical Trial Ops tools (demo mode, no API key)."""
import os, sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from tools import study_briefer, quality_checker, tmf_analyzer, query_drafter, risk_scorer

# All numbers in _STATE must be int or already present as-is in the JSON corpus.
# visit_completion_pct deliberately omitted from brief output (computed, may not match corpus).
_STATE = {
    "study_id": "DEMO-STUDY-001",
    "protocol_id": "PROTO-XR-301",
    "sponsor": "Demo Pharma Inc.",
    "review_period": "2026-Q1",
    "study_status": {
        "enrolled_subjects": 124,
        "target_enrollment": 200,
        "active_sites": 8,
    },
    "tmf_data": {
        "completeness_pct": 87,
        "missing_documents": ["Site Activation Log - Site 04"],
        "last_reviewed": "2026-01-15",
    },
    "tmf_analysis": {
        "completeness_pct": 87,
        "inspection_risk": "HIGH",
        "critical_gaps": [],
        "major_gaps": ["Site Activation Log - Site 04"],
        "minor_gaps": [],
    },
    "enrollment_metrics": {
        "enrolled": 124,
        "target": 200,
        "enrollment_pct": 62,
        "total_open_queries": 3,
        "query_rate": 0.75,
        "visit_completion_pct": 58,
        "tmf_completeness_pct": 87,
    },
    "risk_score": {
        "composite_score": 45,
        "risk_tier": "HIGH",
        "factors": ["enrollment significantly behind (62% of target)"],
        "recommendations": [
            "review site activation and screen failure root causes; consider adding sites"
        ],
    },
    "subject_data": [
        {"subject_id": "001-001", "site_id": "SITE-01", "status": "ACTIVE",
         "visit": "Week 12", "missing_fields": ["Weight"],
         "visits_completed": 4, "visits_expected": 6, "open_queries": 2},
    ],
    "missing_data_flags": [
        {"subject_id": "001-001", "site_id": "SITE-01", "visit": "Week 12",
         "description": "Missing CRF field 'Weight' at Week 12", "severity": "MINOR"},
    ],
    "deviation_flags": [],
    "query_summary": {"total": 1, "critical": 0, "major": 0, "minor": 1,
                      "sites_affected": ["SITE-01"]},
}


# ── tmf_analyzer ──────────────────────────────────────────────────────────────

def test_tmf_analyze_major_gap():
    tmf = {"completeness_pct": 87, "missing_documents": ["Site Activation Log - Site 04"],
           "last_reviewed": "2026-01-15"}
    result = tmf_analyzer.analyze(tmf)
    assert result["completeness_pct"] == 87
    assert result["inspection_risk"] == "HIGH"
    assert "Site Activation Log - Site 04" in result["major_gaps"]
    assert result["critical_gaps"] == []
    assert not result["inspection_ready"]


def test_tmf_analyze_critical_gap():
    tmf = {"completeness_pct": 91, "missing_documents": ["IRB Correspondence - Site 02"],
           "last_reviewed": "2026-01-01"}
    result = tmf_analyzer.analyze(tmf)
    assert "IRB Correspondence - Site 02" in result["critical_gaps"]
    assert result["inspection_risk"] == "CRITICAL"
    assert not result["inspection_ready"]


def test_tmf_analyze_clean():
    tmf = {"completeness_pct": 98, "missing_documents": [], "last_reviewed": "2026-01-20"}
    result = tmf_analyzer.analyze(tmf)
    assert result["inspection_ready"]
    assert result["inspection_risk"] == "LOW"
    assert result["critical_gaps"] == []


def test_tmf_analyze_very_low_pct():
    tmf = {"completeness_pct": 65, "missing_documents": [], "last_reviewed": "2025-10-01"}
    result = tmf_analyzer.analyze(tmf)
    assert result["inspection_risk"] == "CRITICAL"


# ── query_drafter ─────────────────────────────────────────────────────────────

def test_draft_from_missing_fields_creates_queries():
    flags = [
        {"subject_id": "001-001", "site_id": "SITE-01", "visit": "Week 12",
         "description": "Missing CRF field 'Weight' at Week 12", "severity": "MINOR"},
        {"subject_id": "003-001", "site_id": "SITE-03", "visit": "Week 8",
         "description": "Missing CRF field 'HbA1c_Result' at Week 8", "severity": "MINOR"},
    ]
    queries = query_drafter.draft_from_missing_fields(flags, "STUDY-001", "PROTO-XR-301")
    assert len(queries) == 2
    assert all(q["status"] == "DRAFT" for q in queries)
    assert all(q["requires_approval"] for q in queries)
    assert "PROTO-XR-301" in queries[0]["query_text"]


def test_draft_from_deviation_flags():
    flags = [{"subject_id": "201-001", "site_id": "SITE-21",
              "description": "Missed visit window by more than 3 days",
              "deviation_type": "VISIT_WINDOW", "severity": "MAJOR"}]
    queries = query_drafter.draft_from_deviation_flags(flags, "STUDY-003", "PROTO-ONC-101")
    assert len(queries) == 1
    assert "deviation" in queries[0]["query_text"].lower()
    assert queries[0]["severity"] == "MAJOR"


def test_query_summary_totals():
    queries = [{"severity": "CRITICAL", "site_id": "SITE-01"},
               {"severity": "MAJOR",    "site_id": "SITE-02"},
               {"severity": "MINOR",    "site_id": "SITE-02"}]
    summary = query_drafter.summarize_queries(queries)
    assert summary["total"] == 3
    assert summary["critical"] == 1
    assert summary["major"] == 1
    assert summary["minor"] == 1
    assert "SITE-01" in summary["sites_affected"]


def test_query_summary_empty():
    assert query_drafter.summarize_queries([])["total"] == 0


# ── risk_scorer ───────────────────────────────────────────────────────────────

def test_risk_score_critical():
    result = risk_scorer.score(
        enrolled=30, target_enrollment=200,
        tmf_completeness_pct=71, tmf_critical_gaps=4,
        query_rate=3.5, total_open_queries=15,
        visit_completion_pct=40,
    )
    assert result["risk_tier"] == "CRITICAL"
    assert result["composite_score"] >= 70


def test_risk_score_low():
    result = risk_scorer.score(
        enrolled=185, target_enrollment=200,
        tmf_completeness_pct=97, tmf_critical_gaps=0,
        query_rate=0.3, total_open_queries=5,
        visit_completion_pct=96,
    )
    assert result["risk_tier"] == "LOW"
    assert result["composite_score"] < 20


def test_risk_score_has_four_factors():
    result = risk_scorer.score(
        enrolled=100, target_enrollment=200,
        tmf_completeness_pct=85, tmf_critical_gaps=0,
        query_rate=2.0, total_open_queries=20,
        visit_completion_pct=80,
    )
    assert len(result["factors"]) == 4
    assert "component_scores" in result


def test_risk_recommendations_are_lowercase():
    result = risk_scorer.score(
        enrolled=30, target_enrollment=200,
        tmf_completeness_pct=71, tmf_critical_gaps=0,
        query_rate=3.5, total_open_queries=15,
        visit_completion_pct=40,
    )
    for rec in result["recommendations"]:
        # first char should not be uppercase (all recs are lowercase)
        assert not rec[0].isupper(), f"recommendation starts uppercase: {rec!r}"


# ── study_briefer (demo) ──────────────────────────────────────────────────────

def test_demo_brief_contains_required_elements():
    out = study_briefer.draft_brief(_STATE)
    assert out["drafted_by"].startswith("demo")
    text = out["brief_text"]
    assert "DEMO-STUDY-001" in text
    assert "124" in text
    assert "200" in text
    assert "87" in text
    assert "clinical operations lead" in text.lower()
    assert "no edc queries are issued" in text.lower()


def test_demo_brief_passes_quality_checks():
    out = study_briefer.draft_brief(_STATE)
    findings = quality_checker.quality_findings(out["brief_text"])
    assert findings == [], f"quality findings: {findings}"


def test_demo_brief_is_grounded():
    out = study_briefer.draft_brief(_STATE)
    g = quality_checker.grounding_findings(out["brief_text"], _STATE)
    assert g["grounded"], f"ungrounded: {g}"


# ── quality_checker ───────────────────────────────────────────────────────────

def test_quality_flags_speculative_language():
    bad = "This study is definitely 100% compliant with all requirements."
    findings = quality_checker.quality_findings(bad)
    assert any("speculative" in f for f in findings)


def test_quality_flags_missing_elements():
    incomplete = "The study is going well."
    findings = quality_checker.quality_findings(incomplete)
    assert len(findings) > 0


def test_grounding_flags_invented_number():
    g = quality_checker.grounding_findings("Study enrolled 98765 subjects.", _STATE)
    assert not g["grounded"]


def test_grounding_passes_state_numbers():
    text = (
        "Enrollment: 124 of 200 target subjects enrolled across 8 active sites. "
        "eTMF completeness: 87%. Data review identified 1 missing data point. "
        "Recommended action: review site activation. "
        "Approval by clinical operations lead required before queries are issued."
    )
    g = quality_checker.grounding_findings(text, _STATE)
    assert g["grounded"], f"state numbers should be grounded: {g}"
