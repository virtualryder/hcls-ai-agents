"""Unit tests for Pharmacovigilance ICSR tools (demo mode, no API key)."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from tools import (
    case_extractor,
    coder,
    duplicate_checker,
    seriousness_assessor,
    narrative_drafter,
    quality_checker,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

SERIOUS_RAW = (
    "Dr. Robert Chen, nephrologist, Toronto General Hospital, Canada. "
    "Patient is a 67 year old male receiving Lisinopril 20 mg once daily by oral route "
    "for hypertension. Patient was hospitalized on 2026-01-15 with acute renal failure, "
    "21 days after starting Lisinopril. Creatinine elevated. "
    "Positive dechallenge — renal function improved after discontinuation."
)

NON_SERIOUS_RAW = (
    "Dr. Jane Williams, cardiologist, St. Mary Hospital, United Kingdom. "
    "A 52 year old female patient receiving Metformin 1000 mg by oral route for "
    "type 2 diabetes experienced nausea 14 days after starting therapy. "
    "Patient recovered fully. Possibly related to Metformin."
)

FATAL_RAW = (
    "Literature report — Authors Johnson MK, Patel S. "
    "A 74 year old male patient with atrial fibrillation received Warfarin 5 mg daily "
    "by oral route for anticoagulation. The patient developed intracranial haemorrhage "
    "30 days after initiating Warfarin and died on 2026-02-03. Life-threatening event. "
    "Fatal outcome. Causality: related to Warfarin. Dechallenge: not applicable."
)

_BASE_STATE = {
    "case_id": "ICSR-TEST-001",
    "patient_age": "67 years",
    "patient_sex": "MALE",
    "reporter_name": "Dr. Robert Chen",
    "reporter_type": "HEALTHCARE_PROFESSIONAL",
    "reporter_country": "Canada",
    "suspect_drug": "Lisinopril",
    "whodrug_name": "Lisinopril",
    "whodrug_atc": "C09AA03",
    "suspect_dose": "20 mg",
    "suspect_route": "oral",
    "suspect_indication": "hypertension",
    "event_description": "acute renal failure",
    "meddra_pt": "Renal failure acute",
    "meddra_pt_code": "10038436",
    "meddra_soc": "Renal and urinary disorders",
    "time_to_onset_days": "21",
    "event_onset_date": "2026-01-15",
    "event_outcome": "RECOVERING",
    "dechallenge": "POSITIVE",
    "rechallenge": "UNKNOWN",
    "is_serious": True,
    "seriousness_criteria": ["hospitalization"],
    "expectedness": "UNEXPECTED",
    "reporting_clock_days": 15,
    "causality_assessment": "POSSIBLY_RELATED",
    "raw_source": SERIOUS_RAW,
}


# ── Validity check ─────────────────────────────────────────────────────────────

def test_validity_check_serious_case():
    result = case_extractor.check_validity(SERIOUS_RAW)
    assert result["is_valid_icsr"], f"Should be valid ICSR: {result['validity_notes']}"
    assert result["has_identifiable_patient"]
    assert result["has_identifiable_reporter"]
    assert result["has_suspect_product"]
    assert result["has_adverse_event"]


def test_validity_check_empty_source():
    result = case_extractor.check_validity("")
    assert not result["is_valid_icsr"]
    assert len(result["validity_notes"]) > 0


# ── Field extraction ───────────────────────────────────────────────────────────

def test_extract_fields_serious():
    fields = case_extractor.extract(SERIOUS_RAW)
    assert fields["patient_age"] == "67 years"
    assert fields["patient_sex"] == "MALE"
    assert fields["suspect_dose"] == "20 mg"
    assert fields["time_to_onset_days"] == "21"
    assert fields["reporter_type"] == "HEALTHCARE_PROFESSIONAL"
    assert fields["dechallenge"] == "POSITIVE"


def test_extract_fields_outcome_fatal():
    fields = case_extractor.extract(FATAL_RAW)
    assert fields["event_outcome"] == "FATAL"


def test_extract_fields_reporter_type_literature():
    fields = case_extractor.extract(FATAL_RAW)
    assert fields["reporter_type"] == "LITERATURE"


def test_extract_fields_reporter_type_hcp():
    fields = case_extractor.extract(NON_SERIOUS_RAW)
    assert fields["reporter_type"] == "HEALTHCARE_PROFESSIONAL"


# ── MedDRA + WHODrug demo coding ───────────────────────────────────────────────

def test_meddra_coding_known_event():
    result = coder.code_event_demo("acute renal failure")
    assert result["pt"]
    assert result["pt_code"]
    assert result["soc"]


def test_meddra_coding_hepatotoxicity():
    result = coder.code_event_demo("hepatotoxicity liver injury")
    assert result["pt"] == "Hepatotoxicity"
    assert result["pt_code"] == "10019851"


def test_whodrug_coding_known_drug():
    result = coder.code_drug_demo("Lisinopril")
    assert result["name"] == "Lisinopril"
    assert result["atc"] == "C09AA03"


def test_whodrug_coding_unknown_drug():
    result = coder.code_drug_demo("UnknownDrugXYZ")
    assert result["name"]
    assert result["atc"]


# ── Duplicate detection ────────────────────────────────────────────────────────

def test_duplicate_search_clean_case():
    """A fresh case_id returns no high-confidence duplicates from the demo fixture."""
    state = {**_BASE_STATE, "case_id": "ICSR-NEW-9999"}
    candidates = duplicate_checker.demo_search(state)
    # demo_search returns empty list for non-DUPLICATE case IDs
    assert candidates == [], f"expected no duplicates, got {candidates}"


def test_duplicate_search_flags_duplicate():
    """A case_id containing DUPLICATE returns candidates."""
    state = {**_BASE_STATE, "case_id": "ICSR-DUPLICATE-0001"}
    candidates = duplicate_checker.demo_search(state)
    assert len(candidates) > 0, "duplicate case_id should return candidates"
    assert "case_id" in candidates[0]


# ── Seriousness assessment ─────────────────────────────────────────────────────

def test_seriousness_hospitalization():
    result = seriousness_assessor.assess({**_BASE_STATE, "raw_source": SERIOUS_RAW})
    assert result["is_serious"]
    assert "hospitalization" in result["seriousness_criteria"]
    assert result["reporting_clock_days"] == 15


def test_seriousness_fatal_7day_clock():
    state = {**_BASE_STATE, "raw_source": FATAL_RAW, "event_outcome": "FATAL"}
    result = seriousness_assessor.assess(state)
    assert result["is_serious"]
    assert "death" in result["seriousness_criteria"]
    assert result["reporting_clock_days"] == 7


def test_seriousness_non_serious():
    # Use a minimal raw_source with no seriousness keywords
    raw = (
        "Dr. Jane Williams, cardiologist, St. Mary Hospital. "
        "A 52 year old female patient receiving Metformin 1000 mg by oral route "
        "experienced nausea 14 days after starting therapy. Patient recovered fully."
    )
    state = {**_BASE_STATE, "raw_source": raw, "event_outcome": "RECOVERED",
             "event_description": "nausea"}
    result = seriousness_assessor.assess(state)
    assert not result["is_serious"], f"nausea case should be non-serious; got {result}"
    assert result["seriousness_criteria"] == []
    assert result["reporting_clock_days"] is None


# ── Narrative drafting ─────────────────────────────────────────────────────────

def test_demo_narrative_contains_required_elements():
    out = narrative_drafter.draft_narrative(_BASE_STATE)
    assert out["narrative_drafted_by"].startswith("demo")
    text = out["narrative_text"]
    # who: patient age
    assert "67" in text or "year" in text.lower()
    # who: reporter
    assert "Dr. Robert Chen" in text or "chen" in text.lower()
    # what product with dose
    assert "Lisinopril" in text
    assert "20 mg" in text
    # what event
    assert "renal" in text.lower() or "failure" in text.lower()
    # when: onset days
    assert "21" in text
    # seriousness
    assert "serious" in text.lower()
    # causality
    assert "causal" in text.lower() or "related" in text.lower() or "possibly" in text.lower()
    # closure statement
    assert "sign-off" in text.lower() or "no submission" in text.lower() or "reviewer" in text.lower()


def test_demo_narrative_is_grounded():
    out = narrative_drafter.draft_narrative(_BASE_STATE)
    text = out["narrative_text"]
    result = quality_checker.check({**_BASE_STATE, "narrative_text": text})
    g = result["grounding_report"]
    assert g["grounded"], f"narrative should be grounded; ungrounded: {g}"


# ── Quality check ──────────────────────────────────────────────────────────────

def test_quality_check_clean_narrative():
    out = narrative_drafter.draft_narrative(_BASE_STATE)
    result = quality_checker.check({**_BASE_STATE, "narrative_text": out["narrative_text"]})
    assert result["phi_check_passed"], "PHI check should pass on a clean narrative"
    assert result["required_elements_present"], (
        f"required elements missing: {result['quality_findings']}"
    )
    assert result["grounding_report"]["grounded"]


def test_phi_check_flags_ssn():
    bad_narrative = (
        "Patient SSN: 123-45-6789. A 67 year old male patient reported by a physician "
        "from Canada received Lisinopril 20 mg for hypertension and developed renal failure "
        "21 days after starting therapy. Outcome: recovering. Serious: hospitalization. "
        "Causality: possibly related. No submission has been made."
    )
    result = quality_checker.check({**_BASE_STATE, "narrative_text": bad_narrative})
    assert not result["phi_check_passed"], "SSN pattern should fail PHI check"
    assert any("PHI" in f or "SSN" in f for f in result["quality_findings"])


def test_grounding_flags_invented_number():
    # 9876 is > 12 and not in state — should be flagged as ungrounded
    invented = (
        "A 9876 year old male patient reported by Dr. Robert Chen, a healthcare professional "
        "from Canada, received Lisinopril 20 mg by oral route for hypertension. "
        "The patient experienced renal failure 21 days after therapy onset. "
        "The event was serious (hospitalization). Causality: possibly related. "
        "No submission has been made."
    )
    result = quality_checker.check({**_BASE_STATE, "narrative_text": invented})
    g = result["grounding_report"]
    assert not g["grounded"], f"invented number 9876 should fail grounding; report: {g}"
