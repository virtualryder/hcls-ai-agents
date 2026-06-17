"""
Unit tests for aws-native-reference/02-pharmacovigilance/core.py

All tests run without AWS credentials, Bedrock access, or a model.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import core


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SERIOUS_RAW = (
    "Call center intake — caller is Dr. Robert Chen, nephrologist, Toronto General Hospital, Canada. "
    "Patient is a 67 year old male with hypertension receiving Lisinopril 20 mg once daily by oral "
    "route for hypertension. Patient was hospitalized on 2026-01-15 with acute renal failure, 21 days "
    "after starting Lisinopril. Creatinine elevated to 4.2 mg/dL. Patient required intensive care "
    "and dialysis. The event is considered an unexpected serious adverse reaction. Dechallenge: "
    "Lisinopril was discontinued; renal function improved (positive dechallenge)."
)

FATAL_RAW = (
    "Literature case report: Authors Johnson MK, Patel S. Journal of Clinical Pharmacology, 2026. "
    "A 74 year old male patient with atrial fibrillation received Warfarin 5 mg daily by oral route "
    "for anticoagulation. The patient presented to the emergency room with intracranial haemorrhage "
    "30 days after initiating Warfarin therapy. The event was life-threatening and the patient died "
    "on 2026-02-03 despite intensive care. This was an unexpected fatal serious adverse event with "
    "a 7-day expedited reporting clock. Causality was assessed as related to Warfarin by the treating "
    "physician."
)

NON_SERIOUS_RAW = (
    "From: Dr. Jane Williams, Cardiologist, St. Mary Hospital, United Kingdom. A 52 year old female "
    "patient receiving Metformin 1000 mg twice daily by oral route developed nausea and vomiting "
    "approximately 14 days after starting therapy. The patient recovered fully within 3 days after "
    "the medication was discontinued (positive dechallenge). The event is considered possibly related "
    "to Metformin. This is a spontaneous consumer report."
)

_GOOD_NARRATIVE = (
    "A 67 year old male patient was reported by Dr. Robert Chen, a healthcare professional from Canada. "
    "The patient was receiving Lisinopril, 20 mg via oral, for hypertension. "
    "Approximately 21 days after initiating treatment (onset date: 2026-01-15), "
    "the patient experienced renal failure (MedDRA PT: Renal failure [10038435], "
    "SOC: Renal and urinary disorders). "
    "The event was classified as serious (hospitalization). "
    "Expectedness: unexpected. "
    "Causality as assessed: possibly related. "
    "Dechallenge: positive. "
    "Outcome: recovered. "
    "This case is being processed for sign-off; no submission has been made."
)

_CASE_STATE_SERIOUS = {
    "case_id": "ICSR-2026-0002",
    "is_valid_icsr": True,
    "patient_age": "67 years",
    "patient_sex": "MALE",
    "reporter_name": "Dr. Robert Chen",
    "reporter_type": "HEALTHCARE_PROFESSIONAL",
    "reporter_country": "Canada",
    "suspect_drug": "Lisinopril",
    "whodrug_name": "Lisinopril",
    "suspect_dose": "20 mg",
    "suspect_route": "oral",
    "suspect_indication": "hypertension",
    "event_description": "renal failure",
    "meddra_pt": "Renal failure",
    "meddra_pt_code": "10038435",
    "meddra_soc": "Renal and urinary disorders",
    "time_to_onset_days": "21",
    "event_onset_date": "2026-01-15",
    "event_outcome": "RECOVERED",
    "dechallenge": "POSITIVE",
    "is_serious": True,
    "seriousness_criteria": ["hospitalization"],
    "expectedness": "UNEXPECTED",
    "reporting_clock_days": 15,
    "causality_assessment": "POSSIBLY_RELATED",
}


# ---------------------------------------------------------------------------
# validity_check
# ---------------------------------------------------------------------------
class TestValidityCheck:
    def test_valid_icsr_all_four_elements(self):
        result = core.validity_check(SERIOUS_RAW)
        assert result["is_valid_icsr"] is True
        assert result["has_identifiable_patient"] is True
        assert result["has_identifiable_reporter"] is True
        assert result["has_suspect_product"] is True
        assert result["has_adverse_event"] is True
        assert result["validity_notes"] == []

    def test_missing_product_invalid(self):
        raw = "A patient reported headache to a physician."
        result = core.validity_check(raw)
        assert result["has_suspect_product"] is False
        assert result["is_valid_icsr"] is False
        assert any("product" in n for n in result["validity_notes"])

    def test_missing_event_invalid(self):
        # Sentence has patient + reporter + product but no adverse-event keyword.
        # "informed"/"administered"/"glucose control" do not match _EVENT_RE.
        raw = (
            "A pharmacist informed a subject that 100 mg of Metformin was "
            "administered for glucose control."
        )
        result = core.validity_check(raw)
        assert result["has_adverse_event"] is False
        assert result["is_valid_icsr"] is False
        assert any("adverse event" in n for n in result["validity_notes"])

    def test_empty_string_is_invalid(self):
        result = core.validity_check("")
        assert result["is_valid_icsr"] is False
        assert len(result["validity_notes"]) == 4


# ---------------------------------------------------------------------------
# seriousness_classification
# ---------------------------------------------------------------------------
class TestSeriousnessClassification:
    def test_fatal_case_7_day_clock(self):
        result = core.seriousness_classification(FATAL_RAW, "FATAL")
        assert result["is_serious"] is True
        assert "death" in result["seriousness_criteria"]
        assert result["reporting_clock_days"] == 7

    def test_hospitalization_15_day_clock(self):
        result = core.seriousness_classification(SERIOUS_RAW, "RECOVERED")
        assert result["is_serious"] is True
        assert "hospitalization" in result["seriousness_criteria"]
        assert result["reporting_clock_days"] == 15

    def test_non_serious_no_clock(self):
        result = core.seriousness_classification(NON_SERIOUS_RAW, "RECOVERED")
        assert result["is_serious"] is False
        assert result["reporting_clock_days"] is None

    def test_life_threatening_unexpected_7_day(self):
        text = "patient had life-threatening cardiac arrest after taking drug — unexpected event"
        result = core.seriousness_classification(text, "UNKNOWN")
        assert "life_threatening" in result["seriousness_criteria"]
        assert result["reporting_clock_days"] == 7

    def test_disability_criteria_flagged(self):
        text = (
            "patient experienced permanent disability — stroke following drug intake. "
            "patient reported."
        )
        result = core.seriousness_classification(text, "NOT_RECOVERED")
        assert result["is_serious"] is True

    def test_congenital_criteria(self):
        text = "congenital birth defect detected in neonate. patient reported. doctor noted drug."
        result = core.seriousness_classification(text, "UNKNOWN")
        assert "congenital" in result["seriousness_criteria"]

    def test_other_medically_important_fallback(self):
        text = "medically important event — liver failure following treatment"
        result = core.seriousness_classification(text, "UNKNOWN")
        assert "other_medically_important" in result["seriousness_criteria"]


# ---------------------------------------------------------------------------
# expedited_clock
# ---------------------------------------------------------------------------
class TestExpeditedClock:
    def test_fatal_unexpected_7_days(self):
        assert core.expedited_clock(True, ["death"], "UNEXPECTED") == 7

    def test_life_threatening_unexpected_7_days(self):
        assert core.expedited_clock(True, ["life_threatening"], "UNEXPECTED") == 7

    def test_hospitalization_unexpected_15_days(self):
        assert core.expedited_clock(True, ["hospitalization"], "UNEXPECTED") == 15

    def test_non_serious_no_clock(self):
        assert core.expedited_clock(False, [], "UNEXPECTED") is None

    def test_fatal_expected_15_days(self):
        # Fatal but labeled/expected — 15-day clock (not 7-day)
        assert core.expedited_clock(True, ["death"], "EXPECTED") == 15


# ---------------------------------------------------------------------------
# grounding_findings
# ---------------------------------------------------------------------------
class TestGroundingFindings:
    def test_grounded_number_passes(self):
        corpus = {
            "patient_age": "67 years",
            "time_to_onset_days": "21",
            "meddra_pt_code": "10038435",
        }
        text = "67 year old patient, onset 21 days after treatment"
        assert core.grounding_findings(text, corpus) == []

    def test_ungrounded_number_fails(self):
        corpus = {"patient_age": "67 years"}
        text = "99999 subjects were enrolled"
        findings = core.grounding_findings(text, corpus)
        assert any("99999" in f for f in findings)

    def test_small_number_exempt(self):
        corpus = {}
        # Numbers <= 12 are never flagged
        assert core.grounding_findings("7 days, 3 events, 12 subjects", corpus) == []

    def test_nested_corpus_searched(self):
        corpus = {"seriousness_criteria": ["hospitalization"], "reporting_clock_days": 15}
        text = "15-day expedited reporting clock applies"
        assert core.grounding_findings(text, corpus) == []

    def test_multiple_ungrounded(self):
        corpus = {"age": "30 years"}
        text = "patient is 30 years old. 75000 events and 99000 reports found."
        findings = core.grounding_findings(text, corpus)
        assert len(findings) >= 2


# ---------------------------------------------------------------------------
# phi_check
# ---------------------------------------------------------------------------
class TestPhiCheck:
    def test_clean_text_passes(self):
        assert core.phi_check(
            "The patient was 67 years old and received Lisinopril 20 mg."
        ) == []

    def test_ssn_pattern_flagged(self):
        findings = core.phi_check(
            "Patient SSN: 123-45-6789 was leaked in the narrative."
        )
        assert len(findings) == 1
        assert "PHI LEAK" in findings[0]

    def test_multiple_ssn_still_flagged(self):
        text = "SSN 111-22-3333 and also 444-55-6666 in the narrative."
        findings = core.phi_check(text)
        assert len(findings) >= 1


# ---------------------------------------------------------------------------
# required_elements_check
# ---------------------------------------------------------------------------
class TestRequiredElementsCheck:
    def test_complete_narrative_passes(self):
        missing = core.required_elements_check(_GOOD_NARRATIVE)
        assert missing == [], f"Unexpected missing elements: {missing}"

    def test_missing_closure_flagged(self):
        text = (
            "A 67 year old male patient reported by Dr. Chen. "
            "Received Lisinopril 20 mg via oral route. "
            "Patient experienced renal failure (MedDRA PT) 21 days after therapy. "
            "Event was serious (hospitalization). Causality: possibly related."
        )
        missing = core.required_elements_check(text)
        assert any("closure" in m for m in missing)


# ---------------------------------------------------------------------------
# route
# ---------------------------------------------------------------------------
class TestRoute:
    def test_clean_narrative_routes_to_approve(self):
        result = core.route(_CASE_STATE_SERIOUS, _GOOD_NARRATIVE, 0)
        assert result["action"] == "APPROVE_DRAFT"
        assert result["next"] == "HumanReviewGate"

    def test_phi_leak_escalates(self):
        narrative_with_phi = _GOOD_NARRATIVE + " Patient SSN: 123-45-6789."
        result = core.route(_CASE_STATE_SERIOUS, narrative_with_phi, 0)
        assert result["action"] == "ESCALATE"
        assert len(result["phi_findings"]) >= 1

    def test_invalid_icsr_escalates(self):
        state = dict(_CASE_STATE_SERIOUS)
        state["is_valid_icsr"] = False
        result = core.route(state, _GOOD_NARRATIVE, 0)
        assert result["action"] == "ESCALATE"
        assert "invalid" in result["reason"].lower()

    def test_ungrounded_number_triggers_revision_first_pass(self):
        bad_narrative = _GOOD_NARRATIVE + " Also 987654 additional data points were noted."
        result = core.route(_CASE_STATE_SERIOUS, bad_narrative, 0)
        assert result["action"] == "REVISE"
        assert result["next"] == "Draft"

    def test_ungrounded_number_approves_after_revision_budget(self):
        bad_narrative = _GOOD_NARRATIVE + " Also 987654 additional data points were noted."
        # revision_count >= 1 exhausts the one-revision budget
        result = core.route(_CASE_STATE_SERIOUS, bad_narrative, 1)
        assert result["next"] == "HumanReviewGate"

    def test_phi_escalates_even_after_revision_budget(self):
        narrative_with_phi = _GOOD_NARRATIVE + " SSN 999-88-7777 in narrative."
        # PHI always escalates regardless of revision count
        result = core.route(_CASE_STATE_SERIOUS, narrative_with_phi, 5)
        assert result["action"] == "ESCALATE"
