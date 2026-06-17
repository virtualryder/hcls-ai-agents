"""Tests for the deterministic native core (no AWS, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core

EVIDENCE = {
    "indication": "non-small cell lung cancer",
    "phase": "Phase 2",
    "primary_objective": "evaluate progression-free survival",
    "target_population": "adults with NSCLC",
    "study_design": "Randomized Controlled Trial",
    "guidance_count": 3,
    "total_eligible": 3240,
    "sites_with_data": 14,
    "followup_days": 30,
    "monitoring_days": 90,
    "screening_weeks": 4,
}

STATE = {
    "indication": "non-small cell lung cancer",
    "phase": "Phase 2",
    "primary_objective": "evaluate progression-free survival",
    "target_population": "adults with NSCLC",
    "study_design": "Randomized Controlled Trial",
    "guidance_hits": [{"ref": "ICH E9(R1)", "title": "Statistical Principles"}],
}


def test_clean_draft_routes_to_review():
    draft = (
        "Endpoints: the primary endpoint is progression-free survival. "
        "Secondary endpoint includes patient-reported outcomes. "
        "Eligibility: key inclusion and exclusion criteria for adult NSCLC patients. "
        "Schedule: screening at 4 weeks, follow-up visits at 30 and 90 days. "
        "This draft requires review and approval by a qualified medical or clinical reviewer."
    )
    r = core.route(EVIDENCE, draft, 0, STATE)
    assert r["next"] == "HumanReviewGate"
    assert r["action"] == "APPROVE_DRAFT"


def test_speculative_language_triggers_revision():
    draft = (
        "This protocol guarantees 100% effective treatment for all patients. "
        "Endpoints: primary outcome. Eligibility: adults. "
        "Schedule: visits at baseline. Reviewer must approve."
    )
    r = core.route(EVIDENCE, draft, 0, STATE)
    assert r["next"] == "Draft"
    assert r["action"] == "REVISE"


def test_missing_schedule_triggers_revision():
    draft = (
        "Endpoints: primary endpoint is progression-free survival. "
        "Eligibility: adults with NSCLC, adequate organ function. "
        "Reviewer must approve this draft."
    )
    r = core.route(EVIDENCE, draft, 0, STATE)
    assert r["action"] == "REVISE"
    assert any("schedule" in c for c in r["compliance"])


def test_ungrounded_number_triggers_revision():
    draft = (
        "Endpoints: primary. Eligibility: 99999 eligible patients. "
        "Schedule: visits. Reviewer to approve."
    )
    r = core.route(EVIDENCE, draft, 0, STATE)
    assert r["next"] == "Draft" and r["action"] == "REVISE"
    assert any("99999" in g for g in r["grounding"])


def test_revision_count_exhausted_routes_to_review():
    draft = "Endpoints: primary outcome. Eligibility: adults. Schedule: visits. Reviewer approves."
    r = core.route(EVIDENCE, draft, revision_count=1, state=STATE)
    assert r["next"] == "HumanReviewGate"


def test_regulatory_risk_no_guidance():
    state_no_guidance = {**STATE, "guidance_hits": []}
    draft = (
        "Endpoints: primary endpoint is PFS. Eligibility: adults. "
        "Schedule: screening visit. Reviewer to approve."
    )
    r = core.route(EVIDENCE, draft, 0, state_no_guidance)
    assert "regulatory_risks" in r
    assert any("guidance" in risk.lower() for risk in r["regulatory_risks"])


def test_grounding_flags_invented_number():
    findings = core.grounding_findings("We estimate 99999 eligible patients.", EVIDENCE)
    assert any("99999" in f for f in findings)


def test_grounding_passes_state_numbers():
    # 3240, 14 are in EVIDENCE; values <= 12 are exempt
    findings = core.grounding_findings(
        "De-identified data estimates 3240 patients across 14 sites.", EVIDENCE
    )
    assert findings == [], f"state-grounded numbers should pass: {findings}"
