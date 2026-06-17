# tools/case_extractor.py
# ============================================================
# ICSR case field extractor.
#
# Parses raw adverse-event source records (emails, call-center transcripts,
# literature abstracts) into structured E2B(R3) fields. Uses keyword/pattern
# heuristics in demo mode; production routes through the LLM with grounded
# extraction. Also provides ICSR validity checking (4 mandatory elements).
# ============================================================
from __future__ import annotations

import re
from typing import Any, Dict, List


_PATIENT_RE = re.compile(
    r"\b(?:patient|subject|man|woman|male|female|boy|girl|infant|child|adult)\b", re.I
)
_REPORTER_RE = re.compile(
    r"\b(?:reporter|physician|doctor|nurse|pharmacist|hcp|consumer|patient|caller|author)\b", re.I
)
_PRODUCT_RE = re.compile(
    r"\b(?:drug|medication|medicine|tablet|capsule|injection|dose|mg|mcg|infusion|product)\b", re.I
)
_EVENT_RE = re.compile(
    r"\b(?:adverse|event|reaction|side effect|symptom|sign|experienced|developed|presented|"
    r"reported|death|died|hospitali\w*|liver|cardiac|rash|nausea|vomiting|pain|failure|"
    r"anaphyla|seizure|stroke|bleed|thrombos)\w*", re.I
)

# Extraction patterns
_AGE_RE = re.compile(r"\b(\d{1,3})[- ]?(?:year[s]?[- ]?old|yo|y\.?o\.?|years?)\b", re.I)
_SEX_RE = re.compile(r"\b(male|female|man|woman|boy|girl)\b", re.I)
_DOSE_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|IU)\b", re.I)
_ONSET_RE = re.compile(
    r"\b(\d+)\s*(?:day|week|hour|month)s?\s*(?:after|following|post)\b", re.I
)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")

_SEX_MAP = {
    "male": "MALE", "man": "MALE", "boy": "MALE",
    "female": "FEMALE", "woman": "FEMALE", "girl": "FEMALE",
}

_OUTCOME_KEYWORDS = {
    "fatal": "FATAL", "died": "FATAL", "death": "FATAL",
    "recover": "RECOVERED", "resolved": "RECOVERED",
    "recovering": "RECOVERING", "improving": "RECOVERING",
    "not recovered": "NOT_RECOVERED", "ongoing": "NOT_RECOVERED",
    "unknown": "UNKNOWN",
}

# Reporter-type patterns — ordered from most specific to least specific.
# HCP check comes BEFORE consumer so that "patient" in the source text (which
# is about the patient, not the reporter) does not misclassify the reporter.
_HCP_RE = re.compile(
    r"\b(physician|doctor|nurse|pharmacist|hcp|healthcare|nephrologist|cardiologist|"
    r"neurologist|oncologist|dermatologist|radiologist|surgeon|internist|"
    r"specialist|clinician|practitioner|therapist|dentist|midwife)\b", re.I
)
_LITERATURE_RE = re.compile(
    r"\b(literature|article|paper|journal|publication|authors?)\b", re.I
)
_CONSUMER_RE = re.compile(
    r"\b(consumer|family|caregiver)\b", re.I
)


def check_validity(raw: str) -> Dict[str, Any]:
    """Determine if the source satisfies the 4 ICSR mandatory elements."""
    notes: List[str] = []
    has_patient = bool(_PATIENT_RE.search(raw))
    has_reporter = bool(_REPORTER_RE.search(raw))
    has_product = bool(_PRODUCT_RE.search(raw))
    has_event = bool(_EVENT_RE.search(raw))
    if not has_patient:
        notes.append("no identifiable patient detected")
    if not has_reporter:
        notes.append("no identifiable reporter detected")
    if not has_product:
        notes.append("no suspect product detected")
    if not has_event:
        notes.append("no adverse event detected")
    return {
        "has_identifiable_patient": has_patient,
        "has_identifiable_reporter": has_reporter,
        "has_suspect_product": has_product,
        "has_adverse_event": has_event,
        "is_valid_icsr": has_patient and has_reporter and has_product and has_event,
        "validity_notes": notes,
    }


def extract(raw: str) -> Dict[str, Any]:
    """Extract structured E2B(R3) fields from raw source text."""
    # Patient age
    age_m = _AGE_RE.search(raw)
    patient_age = f"{age_m.group(1)} years" if age_m else None

    # Patient sex
    sex_m = _SEX_RE.search(raw)
    patient_sex = _SEX_MAP.get(sex_m.group(1).lower()) if sex_m else None

    # Dose
    dose_m = _DOSE_RE.search(raw)
    suspect_dose = f"{dose_m.group(1)} {dose_m.group(2)}" if dose_m else None

    # Onset days
    onset_m = _ONSET_RE.search(raw)
    time_to_onset = str(onset_m.group(1)) if onset_m else None

    # Onset date
    date_m = _DATE_RE.search(raw)
    event_onset_date = date_m.group(1) if date_m else None

    # Outcome
    raw_lower = raw.lower()
    event_outcome = "UNKNOWN"
    for kw, val in _OUTCOME_KEYWORDS.items():
        if kw in raw_lower:
            event_outcome = val
            break

    # Dechallenge
    dechallenge = "UNKNOWN"
    if re.search(r"\b(dechallenge|discontinued|stopped)\b", raw, re.I):
        dechallenge = "POSITIVE" if re.search(r"\b(improved|resolv)\w*", raw, re.I) else "NEGATIVE"
    if re.search(r"\bnot discontinued\b", raw, re.I):
        dechallenge = "NOT_APPLICABLE"
    if re.search(r"\bnot applicable\b.*dechallenge|dechallenge.*\bnot applicable\b", raw, re.I):
        dechallenge = "NOT_APPLICABLE"

    # Reporter type — check from most specific to least specific so that
    # the word "patient" (referring to the *patient*, not the reporter)
    # does not misclassify a healthcare-professional or literature reporter.
    if _LITERATURE_RE.search(raw):
        reporter_type = "LITERATURE"
    elif _HCP_RE.search(raw):
        reporter_type = "HEALTHCARE_PROFESSIONAL"
    elif _CONSUMER_RE.search(raw):
        reporter_type = "CONSUMER"
    else:
        reporter_type = "OTHER"

    # Drug name (first capitalized word before mg/dose hint)
    drug_m = re.search(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)?)\s+(?:\d+\s*mg|\d+\s*mcg)", raw)
    suspect_drug = drug_m.group(1) if drug_m else _guess_drug(raw)

    # Event (first EVENT_RE match context)
    ev_m = _EVENT_RE.search(raw)
    event_description = ev_m.group(0) if ev_m else "adverse event"

    return {
        "patient_age": patient_age,
        "patient_sex": patient_sex,
        "patient_weight_kg": None,
        "patient_relevant_history": None,
        "reporter_type": reporter_type,
        "suspect_dose": suspect_dose,
        "time_to_onset_days": time_to_onset,
        "event_onset_date": event_onset_date,
        "event_outcome": event_outcome,
        "dechallenge": dechallenge,
        "rechallenge": "UNKNOWN",
        "suspect_drug": suspect_drug,
    }


def _guess_drug(raw: str) -> str:
    """Best-effort drug name extraction from capitalized terms."""
    m = re.search(r"\b([A-Z][a-z]{3,}(?:mab|nib|tide|pril|sartan|vir|olol|statin)?)\b", raw)
    return m.group(1) if m else "Unknown Drug"
