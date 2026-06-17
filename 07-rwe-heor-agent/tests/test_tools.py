"""Unit tests for RWE/HEOR tools (demo mode, no API key). ~20 tests."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from tools import (
    cohort_definer,
    cohort_query_runner,
    data_quality_assessor,
    evidence_synthesizer,
    rwe_checker,
)

# ── Shared fixtures ────────────────────────────────────────────────────────────

_STATE_DIABETES = {
    "request_id": "RWE-TEST-001",
    "research_question": "Does SGLT2 inhibitor reduce hospitalization vs DPP4 inhibitor in T2D?",
    "study_design_type": "Retrospective Cohort",
    "indication": "type 2 diabetes",
    "intervention": "SGLT2 inhibitor",
    "comparator": "DPP4 inhibitor",
    "outcome": "all-cause hospitalization",
    "time_horizon": "12 months",
    "data_source": "US Commercial Claims",
    "cohort_results": {
        "query_id": "RWE-DEMO-001",
        "n_intervention": 4821,
        "n_comparator": 4756,
        "median_follow_up_months": 14,
        "outcome_rate_intervention": "12.4%",
        "outcome_rate_comparator": "18.7%",
        "hazard_ratio": 0.64,
        "ci_lower": 0.52,
        "ci_upper": 0.79,
        "p_value": "<0.001",
        "phi_note": "Aggregate de-identified.",
        "data_completeness_pct": 94,
        "missing_data_note": "formulary data missing for 6% of index prescriptions",
    },
    "summary_statistics": {
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
    },
    "data_quality": {
        "quality_score": 94,
        "concerns": [],
        "warnings": [],
        "cohort_balance": "BALANCED",
        "confounding_flags": ["metabolic confounders likely"],
        "cell_suppression_required": False,
    },
}


# ── Cohort definer ─────────────────────────────────────────────────────────────

def test_cohort_definer_produces_required_fields():
    cd = cohort_definer.define_cohort(_STATE_DIABETES)
    assert cd["indication"] == "type 2 diabetes"
    assert cd["intervention"] == "SGLT2 inhibitor"
    assert cd["comparator"] == "DPP4 inhibitor"
    assert cd["study_design"] == "Retrospective Cohort"
    assert "washout_period" in cd
    assert "exclusions" in cd


def test_cohort_definer_icd10_codes_for_diabetes():
    cd = cohort_definer.define_cohort(_STATE_DIABETES)
    codes = cd.get("indication_codes", {})
    assert "E11" in codes.get("icd10", [])


def test_cohort_definer_validates_complete():
    cd = cohort_definer.define_cohort(_STATE_DIABETES)
    v = cohort_definer.validate_cohort_definition(cd)
    assert v["valid"], f"validation issues: {v['issues']}"
    assert v["issues"] == []


def test_cohort_definer_validates_incomplete():
    v = cohort_definer.validate_cohort_definition({"indication": "type 2 diabetes"})
    assert not v["valid"]
    assert len(v["issues"]) > 0


# ── Cohort query runner ────────────────────────────────────────────────────────

def test_demo_query_returns_diabetes_fixture():
    result = cohort_query_runner.run_demo_query({
        "intervention": "SGLT2 inhibitor",
        "comparator": "DPP4 inhibitor",
    })
    assert result["n_intervention"] == 4821
    assert result["n_comparator"] == 4756
    assert "phi_note" in result


def test_demo_query_returns_psoriasis_fixture():
    result = cohort_query_runner.run_demo_query({
        "intervention": "IL-17A inhibitor",
        "comparator": "TNF-alpha inhibitor",
    })
    assert result["n_intervention"] == 1823


def test_demo_query_returns_default_for_unknown():
    result = cohort_query_runner.run_demo_query({
        "intervention": "unknown-drug",
        "comparator": "placebo",
    })
    assert "n_intervention" in result
    assert result["n_intervention"] > 0


def test_compute_summary_statistics_extracts_correctly():
    cohort = {"n_intervention": 4821, "n_comparator": 4756,
              "outcome_rate_intervention": "12.4%", "outcome_rate_comparator": "18.7%",
              "hazard_ratio": 0.64, "ci_lower": 0.52, "ci_upper": 0.79,
              "p_value": "<0.001", "data_completeness_pct": 94}
    stats = cohort_query_runner.compute_summary_statistics(cohort)
    assert stats["n_intervention"] == 4821
    assert stats["hazard_ratio"] == 0.64
    assert "note" in stats


def test_compute_summary_flags_cell_suppression():
    cohort = {"n_intervention": 5, "n_comparator": 100}
    stats = cohort_query_runner.compute_summary_statistics(cohort)
    assert "cell_suppression_warning" in stats


# ── Data quality assessor ──────────────────────────────────────────────────────

def test_data_quality_high_completeness():
    cohort = {"data_completeness_pct": 94, "n_intervention": 4821,
              "n_comparator": 4756, "indication": "type 2 diabetes"}
    qa = data_quality_assessor.assess_data_quality(cohort)
    assert qa["quality_score"] >= 80
    assert qa["cohort_balance"] == "BALANCED"
    assert not qa["cell_suppression_required"]


def test_data_quality_low_completeness_flags_concern():
    cohort = {"data_completeness_pct": 60, "n_intervention": 500,
              "n_comparator": 500, "indication": "type 2 diabetes"}
    qa = data_quality_assessor.assess_data_quality(cohort)
    assert any("60%" in c for c in qa["concerns"])


def test_data_quality_cell_suppression_small_n():
    cohort = {"data_completeness_pct": 95, "n_intervention": 5,
              "n_comparator": 200, "indication": "psoriasis"}
    qa = data_quality_assessor.assess_data_quality(cohort)
    assert qa["cell_suppression_required"]
    assert any("N=5" in c or "< 11" in c or "minimum" in c for c in qa["concerns"])


# ── Evidence synthesizer ───────────────────────────────────────────────────────

def test_demo_synthesis_contains_required_elements():
    out = evidence_synthesizer.draft_synthesis(_STATE_DIABETES)
    assert out["drafted_by"].startswith("demo")
    text = out["evidence_synthesis"]
    assert "4821" in text or "n_intervention" in text.lower() or "4821" in text
    assert "4756" in text or str(4756) in text
    assert "12 months" in text
    assert "association" in text.lower() or "observational" in text.lower()
    assert "epidemiologist" in text.lower()


def test_demo_synthesis_is_grounded():
    out = evidence_synthesizer.draft_synthesis(_STATE_DIABETES)
    text = out["evidence_synthesis"]
    g = rwe_checker.grounding_findings(text, _STATE_DIABETES)
    assert g["grounded"], f"synthesis should be grounded; report: {g}"


# ── RWE checker ───────────────────────────────────────────────────────────────

def test_quality_clean_synthesis():
    out = evidence_synthesizer.draft_synthesis(_STATE_DIABETES)
    findings = rwe_checker.quality_findings(out["evidence_synthesis"])
    assert findings == [], f"unexpected findings: {findings}"


def test_quality_flags_causal_language():
    bad = "This study proves causation — SGLT2i definitively demonstrates superiority."
    findings = rwe_checker.quality_findings(bad)
    assert any("causal" in f for f in findings)


def test_grounding_flags_invented_number():
    g = rwe_checker.grounding_findings("We found 99999 patients in the cohort.", _STATE_DIABETES)
    assert not g["grounded"], f"99999 should fail grounding"


def test_grounding_passes_on_valid_numbers():
    text = (
        "the SGLT2 inhibitor cohort included 4821 patients; "
        "the DPP4 inhibitor cohort included 4756 patients. "
        "the hospitalization rate was 12.4% versus 18.7%. "
        "association is established; causality is not demonstrated. "
        "an epidemiologist must review before publication."
    )
    g = rwe_checker.grounding_findings(text, _STATE_DIABETES)
    assert g["grounded"], f"valid numbers should pass grounding; report: {g}"
