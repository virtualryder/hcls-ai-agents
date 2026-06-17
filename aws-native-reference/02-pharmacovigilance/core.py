"""
Deterministic core for the Pharmacovigilance ICSR native rebuild.

All non-LLM logic lives here so it can run in Lambdas, be unit-tested without
a model, and remain auditable under ICH E2A / GVP Module VI / 21 CFR Part 314.

Pipeline decides:
  validity_check   — 4 mandatory ICSR elements (patient, reporter, product, event)
  seriousness      — ICH E2A criteria: death / life_threatening / hospitalization /
                     disability / congenital / other_medically_important
  expedited_clock  — 7-day (fatal/life-threatening unexpected) | 15-day (other serious
                     unexpected) | None (non-serious)
  grounding        — numbers > 12 in the narrative must appear in the case-state corpus
  phi_check        — raw SSN pattern is a fatal PHI leak; escalate immediately
  route()          — APPROVE_DRAFT | REVISE | ESCALATE

No model, no AWS dependencies.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Validity — 4 mandatory ICSR elements (ICH E2A)
# ---------------------------------------------------------------------------
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
    r"\b(?:adverse|event|reaction|side\s+effect|symptom|sign|experienced|developed|presented|"
    r"reported|death|died|hospitali\w*|liver|cardiac|rash|nausea|vomiting|pain|failure|"
    r"anaphyla|seizure|stroke|bleed|thrombos)\w*",
    re.I,
)


def validity_check(raw: str) -> Dict[str, Any]:
    """
    Return has_identifiable_patient/reporter/suspect_product/adverse_event and
    is_valid_icsr (True only when all four are present).
    """
    has_patient = bool(_PATIENT_RE.search(raw))
    has_reporter = bool(_REPORTER_RE.search(raw))
    has_product = bool(_PRODUCT_RE.search(raw))
    has_event = bool(_EVENT_RE.search(raw))
    notes: List[str] = []
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


# ---------------------------------------------------------------------------
# Seriousness classification — ICH E2A
# ---------------------------------------------------------------------------
_DEATH_RE = re.compile(r"\b(fatal|died|death|deceased|lethal)\b", re.I)
_LIFE_THREATENING_RE = re.compile(
    r"\b(life[- ]threatening|cardiac arrest|respiratory arrest|anaphyla\w*|"
    r"status epilepticus|septic shock|hemorrhagic shock)\b",
    re.I,
)
_HOSPITALIZATION_RE = re.compile(
    r"\b(hospitali\w+|admitted|admission|icu|intensive care|inpatient|"
    r"emergency room|er visit|a&e)\b",
    re.I,
)
_DISABILITY_RE = re.compile(
    r"\b(disab\w*|incapacitat\w*|permanent|paralys\w*|paraly[sz]\w*|stroke|"
    r"blindness|deafness)\b",
    re.I,
)
_CONGENITAL_RE = re.compile(
    r"\b(congenital|birth defect|fetal|foetal|neonatal|teratogen\w*)\b", re.I
)
_MEDICALLY_IMPORTANT_RE = re.compile(
    r"\b(medically important|important medical event|intervention|liver failure|"
    r"renal failure|bone marrow suppression|drug[- ]induced|sjs|toxic epidermal)\b",
    re.I,
)
_UNEXPECTED_RE = re.compile(r"\b(unexpected|unlabeled|not.*label\w*|not.*smpc)\b", re.I)
_EXPECTED_RE = re.compile(r"\b(expected|labeled|in.*smpc|in.*\bpi\b)\b", re.I)


def seriousness_classification(text: str, event_outcome: str = "UNKNOWN") -> Dict[str, Any]:
    """
    Classify seriousness from combined text (raw_source + event_description).
    Returns criteria list, is_serious, expectedness, reporting_clock_days.
    """
    criteria: List[str] = []
    if _DEATH_RE.search(text) or event_outcome == "FATAL":
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

    expectedness = "EXPECTED" if _EXPECTED_RE.search(text) else "UNEXPECTED"

    reporting_clock_days: Optional[int] = None
    if is_serious:
        if ("death" in criteria or "life_threatening" in criteria) and expectedness == "UNEXPECTED":
            reporting_clock_days = 7
        else:
            reporting_clock_days = 15

    return {
        "is_serious": is_serious,
        "seriousness_criteria": criteria,
        "expectedness": expectedness,
        "reporting_clock_days": reporting_clock_days,
    }


def expedited_clock(is_serious: bool, criteria: List[str], expectedness: str) -> Optional[int]:
    """
    Standalone helper — returns 7 | 15 | None.
    7  days : fatal or life-threatening, unexpected
    15 days : other serious unexpected
    None    : non-serious
    """
    if not is_serious:
        return None
    if ("death" in criteria or "life_threatening" in criteria) and expectedness == "UNEXPECTED":
        return 7
    return 15


# ---------------------------------------------------------------------------
# Grounding
# ---------------------------------------------------------------------------
_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")


def grounding_findings(text: str, corpus: Dict[str, Any]) -> List[str]:
    """
    Numbers > 12 in the narrative must appear verbatim in the corpus.
    Designed to catch invented numbers while ignoring common small values
    (ages ≤ 12, dose fragments, etc. that are ubiquitous).
    """
    flat = " ".join(str(v) for v in _flatten(corpus))
    corpus_nums = set(_NUM.findall(flat))
    out: List[str] = []
    for tok in _NUM.findall(text):
        try:
            if float(tok) <= 12:
                continue
        except ValueError:
            continue
        if tok not in corpus_nums:
            out.append(f"ungrounded number: {tok}")
    return out


def _flatten(obj: Any) -> List[Any]:
    if isinstance(obj, dict):
        vals: List[Any] = []
        for v in obj.values():
            vals += _flatten(v)
        return vals
    if isinstance(obj, list):
        vals = []
        for v in obj:
            vals += _flatten(v)
        return vals
    return [obj]


# ---------------------------------------------------------------------------
# PHI check
# ---------------------------------------------------------------------------
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def phi_check(text: str) -> List[str]:
    """Return a list of PHI findings. Empty list means PHI-clean."""
    findings: List[str] = []
    if _SSN_RE.search(text):
        findings.append("PHI LEAK: raw SSN pattern detected in narrative — ESCALATE")
    return findings


# ---------------------------------------------------------------------------
# Required narrative elements (ICH E2B(R3))
# ---------------------------------------------------------------------------
_REQUIRED_NARRATIVE = {
    "who_patient": re.compile(
        r"\b(patient|subject|man|woman|male|female|boy|girl|infant|child|adult|age|year[s]?[- ]old)\b",
        re.I,
    ),
    "who_reporter": re.compile(
        r"\b(reporter|physician|doctor|nurse|pharmacist|hcp|consumer|literature|author|reported by)\b",
        re.I,
    ),
    "what_product": re.compile(
        r"\b(mg|mcg|dose|drug|medication|tablet|capsule|injection|route|oral|intravenous|subcutaneous)\b",
        re.I,
    ),
    "what_event": re.compile(
        r"\b(adverse|event|reaction|experienced|developed|presented|symptom|sign|MedDRA|PT)\b",
        re.I,
    ),
    "when_onset": re.compile(
        r"\b(day[s]?|week[s]?|hour[s]?|onset|after|following|approximately|duration)\b", re.I
    ),
    "seriousness": re.compile(
        r"\b(serious|non[- ]serious|death|fatal|life[- ]threatening|hospitali[sz]|disab|"
        r"seriousness|congenital)\b",
        re.I,
    ),
    "causality": re.compile(r"\b(causalit|related|possibly|unrelated|unknown|assess)\w*", re.I),
    "closure": re.compile(
        r"\b(sign[- ]off|no submission|reviewer|pending|being processed)\b", re.I
    ),
}


def required_elements_check(text: str) -> List[str]:
    """Return missing required narrative elements. Empty list means all present."""
    missing: List[str] = []
    for element, pat in _REQUIRED_NARRATIVE.items():
        if not pat.search(text):
            missing.append(f"missing required narrative element: {element}")
    return missing


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def route(
    case_state: Dict[str, Any],
    narrative: str,
    revision_count: int,
) -> Dict[str, Any]:
    """
    Deterministic routing decision.

    Priority order:
    1. PHI leak in narrative            → ESCALATE (fatal — never allow forward)
    2. ICSR invalid (missing elements)  → ESCALATE (cannot file an invalid case)
    3. Ungrounded numbers / missing
       narrative elements, revision < 1 → REVISE
    4. Otherwise                        → APPROVE_DRAFT (→ HumanReviewGate)
    """
    # Build corpus from case_state for grounding
    corpus = {k: v for k, v in case_state.items() if k != "raw_source"}

    phi = phi_check(narrative)
    grnd = grounding_findings(narrative, corpus)
    missing_elem = required_elements_check(narrative)

    # Fatal escalation conditions
    if phi:
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "phi_findings": phi,
            "grounding_findings": grnd,
            "missing_elements": missing_elem,
            "reason": "PHI leak detected",
        }

    if not case_state.get("is_valid_icsr", True):
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "phi_findings": phi,
            "grounding_findings": grnd,
            "missing_elements": missing_elem,
            "reason": "ICSR invalid — missing mandatory case elements",
        }

    # Revise if quality issues exist and we haven't exceeded the revision budget
    if (grnd or missing_elem) and revision_count < 1:
        return {
            "next": "Draft",
            "action": "REVISE",
            "phi_findings": phi,
            "grounding_findings": grnd,
            "missing_elements": missing_elem,
            "reason": "quality issues detected; requesting revision",
        }

    # Clean (or exhausted revisions) — send to human review
    return {
        "next": "HumanReviewGate",
        "action": "APPROVE_DRAFT",
        "phi_findings": phi,
        "grounding_findings": grnd,
        "missing_elements": missing_elem,
        "reason": "quality checks passed",
    }
