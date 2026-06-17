"""
Assemble Lambda — validates the raw ICSR source, extracts E2B(R3) fields,
applies MedDRA / WHODrug demo coding, and assembles the case_state that flows
through the rest of the Step Functions pipeline.

This replaces the LangGraph nodes: intake + validity_check + extract_fields +
code_terms in a single idempotent Lambda.  All values are sourced from the
input event; no external API calls in demo mode.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

# Allow parent-package imports at deploy time and in tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok

import core

# ---------------------------------------------------------------------------
# Inline demo coders (no external dependency)
# ---------------------------------------------------------------------------
_MEDDRA_FIXTURE = {
    "liver":      ("Hepatotoxicity", "10019851", "Hepatobiliary disorders"),
    "hepat":      ("Hepatotoxicity", "10019851", "Hepatobiliary disorders"),
    "rash":       ("Rash", "10037844", "Skin and subcutaneous tissue disorders"),
    "nausea":     ("Nausea", "10028813", "Gastrointestinal disorders"),
    "vomit":      ("Vomiting", "10047700", "Gastrointestinal disorders"),
    "cardiac":    ("Cardiac failure", "10007554", "Cardiac disorders"),
    "heart":      ("Cardiac failure", "10007554", "Cardiac disorders"),
    "anaphyla":   ("Anaphylactic reaction", "10002198", "Immune system disorders"),
    "seizure":    ("Seizure", "10039906", "Nervous system disorders"),
    "stroke":     ("Cerebrovascular accident", "10008190", "Nervous system disorders"),
    "bleed":      ("Haemorrhage", "10018965", "Vascular disorders"),
    "haemorrh":   ("Haemorrhage", "10018965", "Vascular disorders"),
    "intracrani": ("Intracranial haemorrhage", "10022763", "Nervous system disorders"),
    "thrombos":   ("Deep vein thrombosis", "10051055", "Vascular disorders"),
    "pain":       ("Pain", "10033371", "General disorders and administration site conditions"),
    "death":      ("Death", "10011906", "General disorders and administration site conditions"),
    "died":       ("Death", "10011906", "General disorders and administration site conditions"),
    "fatal":      ("Death", "10011906", "General disorders and administration site conditions"),
    "hospitali":  ("Hospitalisation", "10020751", "General disorders and administration site conditions"),
    "failure":    ("Organ failure", "10030302", "General disorders and administration site conditions"),
    "renal":      ("Renal failure", "10038435", "Renal and urinary disorders"),
}
_DEFAULT_MEDDRA = ("Adverse drug reaction", "10001718",
                   "General disorders and administration site conditions")

_WHODRUG_FIXTURE = {
    "metformin":       ("Metformin", "A10BA02"),
    "atorvastatin":    ("Atorvastatin", "C10AA05"),
    "lisinopril":      ("Lisinopril", "C09AA03"),
    "warfarin":        ("Warfarin", "B01AA03"),
    "amoxicillin":     ("Amoxicillin", "J01CA04"),
    "ibuprofen":       ("Ibuprofen", "M01AE01"),
    "aspirin":         ("Aspirin", "B01AC06"),
    "paracetamol":     ("Paracetamol", "N02BE01"),
    "acetaminophen":   ("Paracetamol", "N02BE01"),
    "omeprazole":      ("Omeprazole", "A02BC01"),
    "simvastatin":     ("Simvastatin", "C10AA01"),
    "amlodipine":      ("Amlodipine", "C08CA01"),
    "rivaroxaban":     ("Rivaroxaban", "B01AF01"),
    "apixaban":        ("Apixaban", "B01AF02"),
    "infliximab":      ("Infliximab", "L04AB02"),
    "adalimumab":      ("Adalimumab", "L04AB04"),
}
_DEFAULT_WHODRUG = ("Unspecified drug", "N07XX99")


def _code_meddra(event_term: str) -> tuple:
    lower = event_term.lower()
    for kw, vals in _MEDDRA_FIXTURE.items():
        if kw in lower:
            return vals
    return _DEFAULT_MEDDRA


def _code_whodrug(drug_name: str) -> tuple:
    lower = drug_name.lower()
    for kw, vals in _WHODRUG_FIXTURE.items():
        if kw in lower:
            return vals
    return _DEFAULT_WHODRUG


# ---------------------------------------------------------------------------
# Extraction helpers (E2B R3 field extraction from raw text)
# ---------------------------------------------------------------------------
_AGE_RE = re.compile(r"\b(\d{1,3})[- ]?(?:year[s]?[- ]?old|yo|y\.?o\.?|years?)\b", re.I)
_SEX_RE = re.compile(r"\b(male|female|man|woman|boy|girl)\b", re.I)
_SEX_MAP = {
    "male": "MALE", "man": "MALE", "boy": "MALE",
    "female": "FEMALE", "woman": "FEMALE", "girl": "FEMALE",
}
_DOSE_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|IU)\b", re.I)
_ONSET_RE = re.compile(r"\b(\d+)\s*(?:day|week|hour|month)s?\s*(?:after|following|post)\b", re.I)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")
_OUTCOME_KW = {
    "fatal": "FATAL", "died": "FATAL", "death": "FATAL",
    "recover": "RECOVERED", "resolved": "RECOVERED",
    "recovering": "RECOVERING", "improving": "RECOVERING",
    "not recovered": "NOT_RECOVERED", "ongoing": "NOT_RECOVERED",
    "unknown": "UNKNOWN",
}
_HCP_RE = re.compile(
    r"\b(physician|doctor|nurse|pharmacist|hcp|healthcare|nephrologist|cardiologist|"
    r"neurologist|oncologist|dermatologist|surgeon|internist|clinician|practitioner)\b",
    re.I,
)
_LIT_RE = re.compile(r"\b(literature|article|paper|journal|publication|authors?)\b", re.I)
_CONSUMER_RE = re.compile(r"\b(consumer|family|caregiver)\b", re.I)
_REPORTER_NAME_RE = re.compile(r"\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.I)
_COUNTRY_RE = re.compile(
    r"\b(United Kingdom|United States|USA|UK|Canada|Germany|France|"
    r"Australia|Japan|Italy|Spain|Netherlands|Sweden|Switzerland)\b",
    re.I,
)


def _extract_fields(raw: str) -> Dict[str, Any]:
    age_m = _AGE_RE.search(raw)
    sex_m = _SEX_RE.search(raw)
    dose_m = _DOSE_RE.search(raw)
    onset_m = _ONSET_RE.search(raw)
    date_m = _DATE_RE.search(raw)

    # Outcome
    raw_lower = raw.lower()
    event_outcome = "UNKNOWN"
    for kw, val in _OUTCOME_KW.items():
        if kw in raw_lower:
            event_outcome = val
            break

    # Dechallenge
    dechallenge = "UNKNOWN"
    if re.search(r"\b(dechallenge|discontinued|stopped)\b", raw, re.I):
        dechallenge = "POSITIVE" if re.search(r"\b(improved|resolv)\w*", raw, re.I) else "NEGATIVE"
    if re.search(r"\bnot applicable\b.*dechallenge|dechallenge.*\bnot applicable\b", raw, re.I):
        dechallenge = "NOT_APPLICABLE"

    # Reporter type
    if _LIT_RE.search(raw):
        reporter_type = "LITERATURE"
    elif _HCP_RE.search(raw):
        reporter_type = "HEALTHCARE_PROFESSIONAL"
    elif _CONSUMER_RE.search(raw):
        reporter_type = "CONSUMER"
    else:
        reporter_type = "OTHER"

    # Reporter name
    rn_m = _REPORTER_NAME_RE.search(raw)
    reporter_name = rn_m.group(0).strip() if rn_m else None

    # Country
    cn_m = _COUNTRY_RE.search(raw)
    reporter_country = cn_m.group(1) if cn_m else "unspecified"

    # Drug name
    drug_m = re.search(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)?)\s+(?:\d+\s*mg|\d+\s*mcg)", raw)
    suspect_drug = drug_m.group(1) if drug_m else _guess_drug(raw)

    # Event
    ev_m = re.search(
        r"\b(?:adverse|event|reaction|experienced|developed|presented|"
        r"haemorrhage|hemorrhage|nausea|vomiting|renal failure|cardiac|seizure|stroke|"
        r"rash|pain|death|thrombos)\w*",
        raw, re.I,
    )
    event_description = ev_m.group(0) if ev_m else "adverse event"

    return {
        "patient_age": f"{age_m.group(1)} years" if age_m else None,
        "patient_sex": _SEX_MAP.get(sex_m.group(1).lower()) if sex_m else None,
        "patient_weight_kg": None,
        "patient_relevant_history": None,
        "reporter_name": reporter_name,
        "reporter_type": reporter_type,
        "reporter_country": reporter_country,
        "suspect_drug": suspect_drug,
        "suspect_dose": f"{dose_m.group(1)} {dose_m.group(2)}" if dose_m else None,
        "suspect_route": "oral",
        "suspect_indication": None,
        "time_to_onset_days": str(onset_m.group(1)) if onset_m else None,
        "event_onset_date": date_m.group(1) if date_m else None,
        "event_outcome": event_outcome,
        "dechallenge": dechallenge,
        "rechallenge": "UNKNOWN",
        "event_description": event_description,
    }


def _guess_drug(raw: str) -> str:
    m = re.search(r"\b([A-Z][a-z]{3,}(?:mab|nib|tide|pril|sartan|vir|olol|statin)?)\b", raw)
    return m.group(1) if m else "Unknown Drug"


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Step Functions input:
    {
      "case_id": "ICSR-2026-0001",
      "source_type": "EMAIL",
      "raw_source": "...",
      "reporter_name": "Dr. Jane Williams",   # optional override
      "reporter_country": "United Kingdom"    # optional override
    }
    """
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    case_id = body.get("case_id", "ICSR-UNKNOWN")
    source_type = body.get("source_type", "UNKNOWN")
    raw_source = body.get("raw_source", "")

    # 1. Validity check
    validity = core.validity_check(raw_source)

    # 2. Extract E2B fields
    fields = _extract_fields(raw_source)

    # Apply explicit overrides from the event (caller may pre-supply some fields)
    for key in ("reporter_name", "reporter_country", "suspect_drug", "patient_age",
                "patient_sex", "suspect_dose", "event_onset_date"):
        if body.get(key):
            fields[key] = body[key]

    # 3. MedDRA coding
    meddra_pt, meddra_pt_code, meddra_soc = _code_meddra(fields["event_description"])
    # 4. WHODrug coding
    whodrug_name, whodrug_atc = _code_whodrug(fields["suspect_drug"] or "")

    # 5. Seriousness assessment
    text = f"{raw_source} {fields['event_description']}"
    seriousness = core.seriousness_classification(text, fields["event_outcome"])

    # 6. Build case_state
    case_state = {
        "case_id": case_id,
        "source_type": source_type,
        "raw_source": raw_source,
        # validity
        **validity,
        # extracted fields
        **fields,
        # coding
        "meddra_pt": meddra_pt,
        "meddra_pt_code": meddra_pt_code,
        "meddra_soc": meddra_soc,
        "whodrug_name": whodrug_name,
        "whodrug_atc": whodrug_atc,
        # seriousness
        **seriousness,
        # pipeline control
        "revision_count": 0,
        "audit_trail": [],
    }

    trail_entry = audit(
        "assemble",
        {
            "case_id": case_id,
            "source_type": source_type,
            "is_valid_icsr": validity["is_valid_icsr"],
            "is_serious": seriousness["is_serious"],
            "reporting_clock_days": seriousness["reporting_clock_days"],
            "meddra_pt": meddra_pt,
            "whodrug_name": whodrug_name,
        },
    )
    case_state["audit_trail"].append(trail_entry)

    return ok(case_state)
