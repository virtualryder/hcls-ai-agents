# tools/seriousness_assessor.py
# ============================================================
# ICSR seriousness classification, expectedness, and reporting clock.
#
# Applies ICH E2A / GVP Module VI criteria deterministically from case state.
# The PV Medical Reviewer confirms or overrides the AI-suggested classification.
#
# Seriousness criteria (ICH E2A):
#   death | life_threatening | hospitalization | disability |
#   congenital | other_medically_important
#
# Reporting clock:
#   7  calendar days  — fatal or life-threatening unexpected SAEs
#   15 calendar days  — all other serious unexpected AEs (expedited)
#   non-serious       — aggregate / periodic reporting (no expedited clock)
# ============================================================
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_DEATH_RE = re.compile(r"\b(fatal|died|death|deceased|lethal)\b", re.I)
_LIFE_THREATENING_RE = re.compile(
    r"\b(life[- ]threatening|cardiac arrest|respiratory arrest|anaphyla\w*|"
    r"status epilepticus|septic shock|hemorrhagic shock)\b", re.I
)
# Use \w* so 'hospitalized' and 'hospitalised' both match without a word-boundary
# after the root (the trailing \b after [sz] would fail before 'ed').
_HOSPITALIZATION_RE = re.compile(
    r"\b(hospitali\w+|admitted|admission|icu|intensive care|inpatient|"
    r"emergency room|er visit|a&e)\b", re.I
)
_DISABILITY_RE = re.compile(
    r"\b(disab\w*|incapacitat\w*|permanent|paralys\w*|paraly[sz]\w*|stroke|"
    r"blindness|deafness)\b", re.I
)
_CONGENITAL_RE = re.compile(
    r"\b(congenital|birth defect|fetal|foetal|neonatal|teratogen\w*)\b", re.I
)
_MEDICALLY_IMPORTANT_RE = re.compile(
    r"\b(medically important|important medical event|intervention|liver failure|"
    r"renal failure|bone marrow suppression|drug[- ]induced|sjs|toxic epidermal)\b", re.I
)
_UNEXPECTED_RE = re.compile(r"\b(unexpected|unlabeled|not.*label\w*|not.*smpc)\b", re.I)
_EXPECTED_RE = re.compile(r"\b(expected|labeled|in.*smpc|in.*\bpi\b)\b", re.I)


def assess(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify seriousness from extracted case fields and raw source.
    Returns is_serious, seriousness_criteria, expectedness, reporting_clock_days,
    and a provisional causality_assessment.
    """
    raw = state.get("raw_source", "")
    event_desc = state.get("event_description", "")
    outcome = state.get("event_outcome", "UNKNOWN")
    text = f"{raw} {event_desc}"

    criteria: List[str] = []

    if _DEATH_RE.search(text) or outcome == "FATAL":
        criteria.append("death")
    if _LIFE_THREATENING_RE.search(text):
        criteria.append("life_threatening")
    if _HOSPITALIZATION_RE.search(text):
        criteria.append("hospitalization")
    if _DISABILITY_RE.search(text) and "death" not in criteria:
        criteria.append("disability")
    if _CONGENITAL_RE.search(text):
        criteria.append("congenital")
    if _MEDICALLY_IMPORTANT_RE.search(text) and not criteria:
        criteria.append("other_medically_important")

    is_serious = len(criteria) > 0

    # Expectedness: default UNEXPECTED unless source explicitly says expected/labeled
    if _EXPECTED_RE.search(text):
        expectedness = "EXPECTED"
    else:
        expectedness = "UNEXPECTED"

    # Reporting clock
    reporting_clock_days: Optional[int] = None
    if is_serious:
        if ("death" in criteria or "life_threatening" in criteria) and expectedness == "UNEXPECTED":
            reporting_clock_days = 7
        else:
            reporting_clock_days = 15

    # Provisional causality (heuristic; PV Medical Reviewer confirms)
    causality = _assess_causality(state)

    return {
        "is_serious": is_serious,
        "seriousness_criteria": criteria,
        "expectedness": expectedness,
        "reporting_clock_days": reporting_clock_days,
        "causality_assessment": causality,
    }


def _assess_causality(state: Dict[str, Any]) -> str:
    """Heuristic provisional causality — PV Medical Reviewer confirms."""
    raw = (state.get("raw_source", "") + " " + state.get("event_description", "")).lower()
    dechallenge = (state.get("dechallenge") or "").upper()
    rechallenge = (state.get("rechallenge") or "").upper()

    if dechallenge == "POSITIVE" and rechallenge == "POSITIVE":
        return "RELATED"
    if dechallenge == "POSITIVE":
        return "POSSIBLY_RELATED"
    if re.search(r"\b(unrelated|coincidental|alternative cause|not related)\b", raw):
        return "UNRELATED"
    if re.search(r"\b(related|caused by|due to|secondary to|consistent with)\b", raw):
        return "POSSIBLY_RELATED"
    return "UNKNOWN"
