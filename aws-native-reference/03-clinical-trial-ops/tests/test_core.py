"""Unit tests for aws-native-reference/03-clinical-trial-ops/core.py"""
from __future__ import annotations

import sys
import os

# Make core importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import core


# ---------------------------------------------------------------------------
# compliance_findings
# ---------------------------------------------------------------------------
class TestComplianceFindings:
    def test_clean_text_passes(self):
        text = (
            "enrollment status: 124 of 200 subjects enrolled. "
            "etmf completeness: 87%. "
            "missing data queries identified at site. "
            "recommended action: review by clinical operations lead."
        )
        assert core.compliance_findings(text) == []

    def test_prohibited_language_flagged(self):
        text = (
            "enrollment status: complete. etmf completeness ok. "
            "missing: none. action: approved. "
            "we guarantee 100% compliance with the protocol."
        )
        issues = core.compliance_findings(text)
        assert any("prohibited" in i for i in issues)

    def test_missing_required_element_flagged(self):
        # omit TMF mention
        text = "enrollment status: 50 subjects. missing data flagged. action: review."
        issues = core.compliance_findings(text)
        assert any("tmf" in i for i in issues)

    def test_all_elements_present(self):
        text = (
            "enrollment: 50 subjects enrolled out of 100. "
            "missing CRF fields flagged as deviations. "
            "eTMF completeness 92%. "
            "recommended action: clinical operations lead to approve."
        )
        assert core.compliance_findings(text) == []


# ---------------------------------------------------------------------------
# grounding_findings
# ---------------------------------------------------------------------------
class TestGroundingFindings:
    def test_grounded_number_passes(self):
        evidence = {"enrolled": 124, "target": 200}
        text = "124 of 200 subjects enrolled"
        assert core.grounding_findings(text, evidence) == []

    def test_ungrounded_number_fails(self):
        evidence = {"enrolled": 50, "target": 100}
        text = "98765 subjects enrolled"
        issues = core.grounding_findings(text, evidence)
        assert any("98765" in i for i in issues)

    def test_small_number_exempt(self):
        evidence = {"enrolled": 5}
        text = "7 subjects"  # <=12, exempt
        assert core.grounding_findings(text, evidence) == []

    def test_nested_evidence_found(self):
        evidence = {"tmf_data": {"completeness_pct": 87}}
        text = "etmf completeness: 87%"
        assert core.grounding_findings(text, evidence) == []


# ---------------------------------------------------------------------------
# tmf_risk
# ---------------------------------------------------------------------------
class TestTmfRisk:
    def test_critical_keyword(self):
        assert core.tmf_risk(["IRB Approval"], 95) == "CRITICAL"

    def test_critical_low_pct(self):
        assert core.tmf_risk([], 70) == "CRITICAL"

    def test_high_missing_major(self):
        # No critical keyword but pct < 90
        assert core.tmf_risk([], 85) == "HIGH"

    def test_medium(self):
        assert core.tmf_risk([], 92) == "MEDIUM"

    def test_low(self):
        assert core.tmf_risk([], 97) == "LOW"


# ---------------------------------------------------------------------------
# risk_score
# ---------------------------------------------------------------------------
class TestRiskScore:
    def test_low_risk(self):
        rs = core.risk_score(90, 100, 97, False, 0.3)
        assert rs["risk_tier"] == "LOW"

    def test_critical_risk(self):
        # Low enrollment + critical TMF
        rs = core.risk_score(10, 200, 70, True, 4.0)
        assert rs["risk_tier"] == "CRITICAL"
        assert rs["composite_score"] >= 70

    def test_composite_components_present(self):
        rs = core.risk_score(50, 100, 88, False, 1.0)
        assert "enrollment" in rs["component_scores"]
        assert "tmf" in rs["component_scores"]
        assert "queries" in rs["component_scores"]


# ---------------------------------------------------------------------------
# route
# ---------------------------------------------------------------------------
class TestRoute:
    def _evidence(self, enrolled=180, target=200, tmf_pct=97, missing=None, query_rate=0.3):
        return {
            "study_id": "TEST-001",
            "enrolled": enrolled,
            "target": target,
            "query_rate": query_rate,
            "tmf_data": {
                "completeness_pct": tmf_pct,
                "missing_documents": missing or [],
            },
        }

    def _clean_draft(self):
        return (
            "enrollment status: 180 of 200 subjects enrolled. "
            "no missing CRF fields flagged. "
            "etmf completeness: 97%. "
            "recommended action: approved by clinical operations lead."
        )

    def test_approve_path(self):
        result = core.route(self._evidence(), self._clean_draft(), 0)
        assert result["next"] == "HumanReviewGate"
        assert result["action"] == "APPROVE_BRIEF"

    def test_revise_path_on_missing_element(self):
        # draft missing "tmf" mention
        draft = (
            "enrollment: 180 of 200 subjects. "
            "missing data queries identified at site. "
            "action: recommended by clinical operations lead."
        )
        result = core.route(self._evidence(), draft, 0)
        assert result["next"] == "Draft"
        assert result["action"] == "REVISE"

    def test_escalate_on_critical_tmf(self):
        ev = self._evidence(enrolled=20, target=200, tmf_pct=70, missing=["IRB Approval"])
        result = core.route(ev, self._clean_draft(), 0)
        assert result["action"] == "ESCALATE"
        assert result["next"] == "HumanReviewGate"

    def test_second_revision_goes_to_hitl(self):
        # After 1 revision, compliance issues should still route to HumanReviewGate
        draft = (
            "enrollment: 180 of 200 subjects. "
            "missing data queries identified at site. "
            "action: recommended by clinical operations lead."
        )
        result = core.route(self._evidence(), draft, 1)
        assert result["next"] == "HumanReviewGate"
