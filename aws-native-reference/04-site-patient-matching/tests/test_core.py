"""Unit tests for aws-native-reference/04-site-patient-matching/core.py"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
import core

_SITE_COUNTS = [
    {"site_id": "SITE-NE-01", "eligible_count": 423, "demographics": {"pct_female": 52, "pct_hispanic": 18, "pct_black": 14}},
    {"site_id": "SITE-SE-01", "eligible_count": 387, "demographics": {"pct_female": 49, "pct_hispanic": 22, "pct_black": 28}},
    {"site_id": "SITE-MW-01", "eligible_count": 312, "demographics": {"pct_female": 48, "pct_hispanic": 9, "pct_black": 11}},
]

def _clean_draft():
    return (
        "site feasibility report for DEMO-STUDY-001. "
        "cohort identified 1847 eligible patients across 6 sites. "
        "top site: SITE-NE-01 (eligible pool: 423). "
        "all patient data is de-identified aggregate; PHI at source systems. "
        "recommended action: approve and initiate outreach."
    )

def _evidence(site_counts=None, total=1847, target=200):
    return {
        "study_id": "DEMO-STUDY-001",
        "target_enrollment": target,
        "cohort_results": {
            "total_eligible": total,
            "site_counts": site_counts or _SITE_COUNTS,
        },
    }

class TestComplianceFindings:
    def test_clean_text_passes(self):
        assert core.compliance_findings(_clean_draft()) == []

    def test_prohibited_language_flagged(self):
        text = _clean_draft() + " this is definitely 100% representative."
        issues = core.compliance_findings(text)
        assert any("prohibited" in i for i in issues)

    def test_missing_phi_note_flagged(self):
        text = "eligible patients found at site. top site ranked. action: review."
        issues = core.compliance_findings(text)
        assert any("phi_note" in i for i in issues)

    def test_all_elements_present(self):
        text = (
            "cohort identified 1847 eligible patients. top site: SITE-NE-01. "
            "all data is de-identified aggregate; PHI at source. "
            "recommended action: approved."
        )
        assert core.compliance_findings(text) == []

class TestGroundingFindings:
    def test_grounded_number_passes(self):
        ev = _evidence()
        assert core.grounding_findings("1847 eligible patients across 6 sites", ev) == []

    def test_ungrounded_number_fails(self):
        ev = _evidence()
        issues = core.grounding_findings("99999 eligible patients found.", ev)
        assert any("99999" in i for i in issues)

    def test_small_number_exempt(self):
        ev = _evidence()
        assert core.grounding_findings("7 sites reviewed", ev) == []

    def test_nested_evidence_found(self):
        ev = {"cohort_results": {"total_eligible": 423}}
        assert core.grounding_findings("423 eligible patients", ev) == []

class TestFairnessFlags:
    def test_under_represented_site_flagged(self):
        sites = [{"site_id": "SITE-MW-01", "eligible_count": 312,
                  "demographics": {"pct_black": 11}}]
        flags = core.fairness_flags(sites)
        assert len(flags) == 1
        assert flags[0]["demographic"] == "Black/African American"

    def test_adequate_representation_no_flag(self):
        sites = [{"site_id": "SITE-SE-01", "eligible_count": 387,
                  "demographics": {"pct_black": 28}}]
        assert core.fairness_flags(sites) == []

    def test_multiple_sites_flagged_correctly(self):
        flags = core.fairness_flags(_SITE_COUNTS)
        flagged = {f["site_id"] for f in flags}
        assert "SITE-MW-01" in flagged
        assert "SITE-SE-01" not in flagged

class TestFeasibilityScore:
    def test_high_coverage_scores_high(self):
        r = core.feasibility_score(total_eligible=2000, target_enrollment=200,
                                   n_sites=6, n_equity_flags=0)
        assert r["tier"] == "HIGH"

    def test_low_coverage_scores_low(self):
        r = core.feasibility_score(total_eligible=100, target_enrollment=1000,
                                   n_sites=1, n_equity_flags=0)
        assert r["tier"] == "LOW"

    def test_equity_penalty_reduces_score(self):
        r_no_flags = core.feasibility_score(1000, 200, 6, 0)
        r_with_flags = core.feasibility_score(1000, 200, 6, 3)
        assert r_with_flags["composite"] < r_no_flags["composite"]

class TestRoute:
    def test_approve_path(self):
        result = core.route(_evidence(), _clean_draft(), 0)
        assert result["next"] == "HumanReviewGate"
        assert result["action"] == "APPROVE_RANKING"

    def test_revise_on_missing_element(self):
        # draft missing phi_note
        draft = "eligible patients at site. top site ranked. action: review."
        result = core.route(_evidence(), draft, 0)
        assert result["next"] == "Draft"
        assert result["action"] == "REVISE"

    def test_escalate_on_critical_equity(self):
        critical_sites = [{"site_id": "X", "eligible_count": 100,
                           "demographics": {"pct_black": 2}}]
        # patch fairness_flags to return CRITICAL
        import unittest.mock as mock
        with mock.patch.object(core, "fairness_flags",
                               return_value=[{"severity": "CRITICAL",
                                              "site_id": "X",
                                              "demographic": "Black/African American",
                                              "site_pct": 2, "benchmark_pct": 13}]):
            result = core.route(_evidence(critical_sites), _clean_draft(), 0)
        assert result["action"] == "ESCALATE"

    def test_second_revision_goes_to_hitl(self):
        draft = "eligible patients at site. top site ranked. action: review."
        result = core.route(_evidence(), draft, 1)
        assert result["next"] == "HumanReviewGate"
