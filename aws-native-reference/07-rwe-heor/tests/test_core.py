"""Tests for the deterministic RWE/HEOR native core (no AWS, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core

_COHORT = {
    "n_intervention": 4821,
    "n_comparator": 4756,
    "median_follow_up_months": 14,
    "outcome_rate_intervention": "12.4%",
    "outcome_rate_comparator": "18.7%",
    "hazard_ratio": 0.64,
    "p_value": "<0.001",
    "data_completeness_pct": 94,
}


def test_clean_synthesis_routes_to_review():
    synthesis = (
        "this retrospective cohort study compared SGLT2 inhibitor versus DPP4 inhibitor. "
        "the SGLT2 inhibitor cohort included 4821 patients; the DPP4 inhibitor cohort included 4756 patients. "
        "median follow-up was 14 months. "
        "the hospitalization rate was 12.4% versus 18.7% (p=<0.001). "
        "these findings establish association and do not demonstrate causality. "
        "limitations: unmeasured confounders may be present. "
        "an epidemiologist must review before publication."
    )
    r = core.route(_COHORT, synthesis, 0)
    assert r["next"] == "HumanReviewGate"
    assert r["action"] == "APPROVE_SYNTHESIS"


def test_causal_language_escalates():
    synthesis = (
        "this study proves causation — SGLT2i causally reduces hospitalization. "
        "4821 patients in intervention group. 4756 in comparator. rate 12.4% vs 18.7%."
    )
    r = core.route(_COHORT, synthesis, 0)
    assert r["action"] == "ESCALATE"
    assert any("causal" in c for c in r["compliance"])


def test_ungrounded_number_triggers_revision():
    synthesis = (
        "we found 99999 patients in the cohort. hospitalization rate was 12.4% versus 18.7%. "
        "these findings establish association only."
    )
    r = core.route(_COHORT, synthesis, 0)
    assert r["next"] == "Synthesize"
    assert r["action"] == "REVISE"
    assert any("99999" in g for g in r["grounding"])


def test_cell_suppression_escalates():
    small_cohort = dict(_COHORT)
    small_cohort["n_intervention"] = 5
    synthesis = "5 patients in intervention. 4756 in comparator. rate 12.4% vs 18.7%."
    r = core.route(small_cohort, synthesis, 0)
    assert r["action"] == "ESCALATE"
    assert any("cell suppression" in c for c in r["compliance"])


def test_low_completeness_flags_warning():
    low_cohort = dict(_COHORT)
    low_cohort["data_completeness_pct"] = 65
    synthesis = (
        "4821 patients in SGLT2 group; 4756 in DPP4 group. rate 12.4% vs 18.7%. "
        "association only; epidemiologist review required."
    )
    r = core.route(low_cohort, synthesis, 0)
    # Low completeness is a compliance warning — triggers REVISE on first pass
    # (not ESCALATE since it's not causal or cell-suppression)
    assert "compliance" in r
    assert any("completeness" in c or "65%" in c for c in r["compliance"])


def test_revision_count_prevents_infinite_loop():
    synthesis = "99999 patients. rate 12.4% vs 18.7%. association only."
    r = core.route(_COHORT, synthesis, revision_count=1)
    # After 1 revision, route to review even if grounding issues remain
    assert r["next"] == "HumanReviewGate"
