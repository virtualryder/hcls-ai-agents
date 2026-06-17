from __future__ import annotations
import os, sys
from pathlib import Path
AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"
import pytest
from tools import eligibility_translator, cohort_estimator, site_ranker, fairness_checker

_STATE = {
    "study_id": "DEMO-STUDY-001",
    "indication": "type 2 diabetes",
    "target_enrollment": 200,
    "cohort_results": {
        "total_eligible": 1847,
        "sites_with_data": 6,
        "site_counts": [
            {"site_id": "SITE-NE-01", "eligible_count": 423,
             "demographics": {"pct_female": 52, "pct_hispanic": 18, "pct_black": 14}},
            {"site_id": "SITE-SE-01", "eligible_count": 387,
             "demographics": {"pct_female": 49, "pct_hispanic": 22, "pct_black": 28}},
        ],
        "phi_note": "All counts are aggregate and de-identified per 45 CFR 164.514.",
    },
    "site_rankings": [
        {"site_id": "SITE-NE-01", "eligible_count": 423, "rank": 1},
        {"site_id": "SITE-SE-01", "eligible_count": 387, "rank": 2},
    ],
    "fairness_flags": [{
        "site_id": "SITE-MW-01",
        "demographic": "Black/African American",
        "description": "Site SITE-MW-01: Black/African American representation (11%) below benchmark.",
        "severity": "MODERATE",
    }],
}


class TestEligibilityTranslator:
    def test_age_criteria_translated(self):
        q = eligibility_translator.translate({"age_min": 18, "age_max": 75}, "type 2 diabetes")
        assert q["cdisc_compliant"] is True
        age_f = [f for f in q["filters"] if f["field"] == "age_years"]
        assert len(age_f) == 2

    def test_diagnosis_codes_in_filters(self):
        q = eligibility_translator.translate({"diagnosis_codes": ["E11", "E11.9"]})
        dx = [f for f in q["filters"] if f["field"] == "icd10_code"]
        assert len(dx) == 1 and "E11" in dx[0]["value"]

    def test_lab_thresholds_translated(self):
        q = eligibility_translator.translate({"lab_thresholds": {"HbA1c": 7.5}})
        assert len(q["labs"]) == 1 and q["labs"][0]["value"] == 7.5

    def test_exclusions_become_exclusion_filters(self):
        q = eligibility_translator.translate({"exclusions": ["active malignancy", "pregnancy"]})
        assert len(q["exclusion_filters"]) == 2

    def test_comorbidity_exclusions_translated(self):
        q = eligibility_translator.translate({"comorbidity_exclusions": ["J84.10"]})
        excl = [f for f in q["exclusion_filters"] if f.get("field") == "icd10_code"]
        assert excl[0]["op"] == "not_in"

    def test_empty_criteria_returns_valid_query(self):
        q = eligibility_translator.translate({})
        assert q["cdisc_compliant"] is True
        assert "all criteria fields translated successfully" in q["translation_notes"]

    def test_summarize_output(self):
        q = eligibility_translator.translate({"age_min": 18, "diagnosis_codes": ["E11"]})
        s = eligibility_translator.summarize(q)
        assert "cdisc-compliant: True" in s


class TestCohortEstimator:
    def test_site_feasible(self):
        r = cohort_estimator.estimate_site("SITE-NE-01", 700, 200)
        assert r["feasible"] is True
        assert "activate" in r["recommendation"]

    def test_zero_eligible_not_feasible(self):
        r = cohort_estimator.estimate_site("X", 0, 200)
        assert r["feasible"] is False
        assert "de-prioritize" in r["recommendation"]

    def test_small_pool_note(self):
        r = cohort_estimator.estimate_site("S", 20, 200)
        assert any("small" in n for n in r["notes"])

    def test_portfolio_feasible(self):
        sites = [{"site_id": "A", "eligible_count": 500},
                 {"site_id": "B", "eligible_count": 400}]
        p = cohort_estimator.estimate_portfolio(sites, 200)
        assert p["portfolio_feasible"] and p["total_projected_enrollees"] > 0

    def test_portfolio_shortfall(self):
        p = cohort_estimator.estimate_portfolio([{"site_id": "T", "eligible_count": 15}], 5000)
        assert not p["portfolio_feasible"] and p["shortfall"] > 0

    def test_top_recommended_sites_capped_at_3(self):
        sites = [{"site_id": str(i), "eligible_count": 500 - i * 50} for i in range(5)]
        p = cohort_estimator.estimate_portfolio(sites, 200)
        assert len(p["top_recommended_sites"]) <= 3


class TestSiteRanker:
    def test_demo_report_clean_and_grounded(self):
        out = site_ranker.draft_report(_STATE)
        assert out["drafted_by"].startswith("demo")
        text = out["ranking_report"]
        assert len(text.split()) >= 30
        assert fairness_checker.quality_findings(text) == []
        g = fairness_checker.grounding_findings(text, _STATE)
        assert g["grounded"], str(g)

    def test_report_mentions_phi_note(self):
        out = site_ranker.draft_report(_STATE)
        t = out["ranking_report"].lower()
        assert "de-identified" in t or "aggregate" in t


class TestFairnessChecker:
    def test_speculative_language_flagged(self):
        findings = fairness_checker.quality_findings(
            "This ranking is definitely 100% representative.")
        assert any("speculative" in f for f in findings)

    def test_clean_text_passes(self):
        ok_text = (
            "The analysis identified 1847 eligible patients across 6 sites. "
            "Top site: SITE-NE-01 (rank 1). "
            "All patient data is de-identified aggregate; PHI at source systems."
        )
        assert fairness_checker.quality_findings(ok_text) == []

    def test_invented_number_flagged(self):
        g = fairness_checker.grounding_findings("We found 99999 eligible patients.", _STATE)
        assert not g["grounded"]

    def test_state_number_grounded(self):
        g = fairness_checker.grounding_findings(
            "The cohort identified 1847 eligible patients across 6 sites.", _STATE)
        assert g["grounded"]
