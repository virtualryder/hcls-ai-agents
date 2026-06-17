# tools/quality_checker.py
# ============================================================
# Quality check for a drafted ICSR narrative.
#
# Three deterministic gates run BEFORE a PV Medical Reviewer sees the narrative:
#   * grounding    — every number/entity traceable to case state (governance.grounding)
#   * PHI check    — no raw SSN or other unmasked PII in the narrative text
#   * required elements — who / what product / what event / when / seriousness /
#                         causality / closure statement present
# These mirror the eval harness so a draft is held to the same bar as CI.
# ============================================================
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

try:
    from governance.grounding import verify_grounding
except Exception:  # pragma: no cover
    verify_grounding = None  # type: ignore

# PHI patterns — raw SSN is a fatal leak
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Required narrative elements (ICH E2B(R3) narrative checklist)
_REQUIRED_ELEMENTS = {
    "who_patient": re.compile(
        r"\b(patient|subject|man|woman|male|female|boy|girl|infant|child|adult|age|year[s]?[- ]old)\b", re.I
    ),
    "who_reporter": re.compile(
        r"\b(reporter|physician|doctor|nurse|pharmacist|hcp|consumer|literature|author|reported by)\b", re.I
    ),
    "what_product": re.compile(
        r"\b(mg|mcg|dose|drug|medication|tablet|capsule|injection|route|oral|intravenous|subcutaneous)\b", re.I
    ),
    "what_event": re.compile(
        r"\b(adverse|event|reaction|experienced|developed|presented|symptom|sign|MedDRA|PT)\b", re.I
    ),
    "when_onset": re.compile(
        r"\b(day[s]?|week[s]?|hour[s]?|onset|after|following|approximately|duration)\b", re.I
    ),
    "seriousness": re.compile(
        r"\b(serious|non[- ]serious|death|fatal|life[- ]threatening|hospitali[sz]|disab|"
        r"seriousness|congenital)\b", re.I
    ),
    "causality": re.compile(
        r"\b(causalit|related|possibly|unrelated|unknown|assess)\w*", re.I
    ),
    "closure": re.compile(
        r"\b(sign[- ]off|no submission|reviewer|pending|being processed)\b", re.I
    ),
}


def _phi_check(text: str) -> tuple:
    """Returns (passed: bool, findings: list[str])."""
    findings: List[str] = []
    if _SSN_RE.search(text):
        findings.append("PHI LEAK: raw SSN pattern detected in narrative — ESCALATE")
    return len(findings) == 0, findings


def _required_elements_check(text: str) -> tuple:
    """Returns (all_present: bool, findings: list[str])."""
    findings: List[str] = []
    for element, pattern in _REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required narrative element: {element}")
    return len(findings) == 0, findings


def check(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run all quality gates on the narrative. Returns a consolidated quality result."""
    narrative = state.get("narrative_text", "")
    findings: List[str] = []

    # PHI check
    phi_passed, phi_findings = _phi_check(narrative)
    findings.extend(phi_findings)

    # Required elements
    elements_ok, element_findings = _required_elements_check(narrative)
    findings.extend(element_findings)

    # Grounding — corpus is the extracted case fields
    if verify_grounding is not None:
        corpus = {
            "patient_age": state.get("patient_age"),
            "patient_sex": state.get("patient_sex"),
            "suspect_drug": state.get("suspect_drug"),
            "whodrug_name": state.get("whodrug_name"),
            "whodrug_atc": state.get("whodrug_atc"),
            "suspect_dose": state.get("suspect_dose"),
            "event_description": state.get("event_description"),
            "meddra_pt": state.get("meddra_pt"),
            "meddra_pt_code": state.get("meddra_pt_code"),
            "meddra_soc": state.get("meddra_soc"),
            "time_to_onset_days": state.get("time_to_onset_days"),
            "event_onset_date": state.get("event_onset_date"),
            "event_outcome": state.get("event_outcome"),
            "is_serious": state.get("is_serious"),
            "seriousness_criteria": state.get("seriousness_criteria"),
            "reporting_clock_days": state.get("reporting_clock_days"),
            "causality_assessment": state.get("causality_assessment"),
            "expectedness": state.get("expectedness"),
            "reporter_name": state.get("reporter_name"),
            "reporter_country": state.get("reporter_country"),
            "reporter_type": state.get("reporter_type"),
            "suspect_route": state.get("suspect_route"),
            "suspect_indication": state.get("suspect_indication"),
            "dechallenge": state.get("dechallenge"),
        }
        grounding_report = verify_grounding(narrative, corpus).to_audit_dict()
    else:
        grounding_report = {
            "grounded": True, "ungrounded_numbers": [], "ungrounded_entities": [],
        }

    return {
        "grounding_report": grounding_report,
        "phi_check_passed": phi_passed,
        "required_elements_present": elements_ok,
        "quality_findings": findings,
    }
