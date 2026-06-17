# tools/root_cause_analyzer.py
# ============================================================
# Root cause analysis tool for the Quality CAPA agent.
#
# Applies rule-based heuristics (5-Why / Ishikawa category mapping)
# to generate structured root-cause hypotheses from:
#   - complaint description
#   - similar historical events
#   - cluster analysis results
# Runs deterministically without an LLM.
# ============================================================
from __future__ import annotations

import re
from typing import Any, Dict, List

# Ishikawa (fishbone) category keywords
_ISHIKAWA: Dict[str, re.Pattern] = {
    "method": re.compile(
        r"\b(procedure|sop|protocol|process|method|step|instruction|work[- ]order)\b", re.I
    ),
    "machine": re.compile(
        r"\b(equipment|machine|filter|pump|hvac|sensor|instrument|calibration|"
        r"maintenance|pm|validation)\b", re.I
    ),
    "material": re.compile(
        r"\b(raw[- ]material|component|excipient|container|vial|batch|lot|"
        r"supplier|vendor|specification)\b", re.I
    ),
    "man": re.compile(
        r"\b(personnel|training|operator|technician|gowning|competency|human[- ]error|"
        r"oversight|communication)\b", re.I
    ),
    "environment": re.compile(
        r"\b(environment|cleanroom|hvac|temperature|humidity|air[- ]quality|"
        r"contamination|microbial|particle)\b", re.I
    ),
    "measurement": re.compile(
        r"\b(test|measurement|monitoring|specification|oos|out[- ]of[- ]spec|"
        r"alarm|threshold|limit)\b", re.I
    ),
}

_IMMEDIATE_CAUSE_KW = {
    "filter integrity": [
        "filter integrity test not performed or not scheduled",
        "filter selection or installation error during batch setup",
    ],
    "gowning": [
        "gowning procedure not followed per standard operating procedure",
        "personnel qualification not current for aseptic areas",
    ],
    "temperature": [
        "monitoring system alarm threshold not correctly configured",
        "preventive maintenance not completed on HVAC or cooling unit",
    ],
    "training": [
        "operator training records not current for this procedure",
        "competency assessment not performed after procedure update",
    ],
    "documentation": [
        "batch record entry not made in real time per procedure",
        "deviation report not initiated within required timeframe",
    ],
}


def _match_category(text: str) -> List[str]:
    """Return Ishikawa categories that match the text."""
    matched: List[str] = []
    for cat, pat in _ISHIKAWA.items():
        if pat.search(text):
            matched.append(cat)
    return matched or ["method"]


def _derive_hypotheses(desc: str, similar: List[Dict[str, Any]]) -> List[str]:
    """Derive root-cause hypotheses from description and similar events."""
    hypotheses: List[str] = []
    combined = desc.lower()
    for ev in similar:
        combined += " " + (ev.get("root_cause") or ev.get("description") or "").lower()

    # Match immediate cause keywords
    for keyword, hlist in _IMMEDIATE_CAUSE_KW.items():
        if keyword in combined:
            hypotheses.extend(hlist[:2])

    # Add Ishikawa-category hypotheses
    categories = _match_category(combined)
    for cat in categories:
        if cat == "machine" and "machine" not in combined:
            hypotheses.append(
                "Equipment or filter maintenance gap contributed to the quality event."
            )
        if cat == "man" and "personnel training" not in " ".join(hypotheses).lower():
            hypotheses.append(
                "Personnel training or competency gap may have contributed."
            )
        if cat == "environment" and "environmental contamination" not in " ".join(hypotheses).lower():
            hypotheses.append(
                "Environmental control failure (HVAC, cleanroom classification) as a contributing factor."
            )

    # Deduplicate while preserving order
    seen: set = set()
    unique: List[str] = []
    for h in hypotheses:
        key = h[:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)

    if not unique:
        unique.append(
            "Root cause to be determined through formal five-why or fishbone investigation."
        )

    return unique[:5]  # cap at 5 hypotheses


def analyze(description: str, similar_events: List[Dict[str, Any]],
            clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform root cause analysis. Returns hypotheses, Ishikawa categories, and
    recurrence risk based on cluster analysis.
    """
    hypotheses = _derive_hypotheses(description, similar_events)
    categories = _match_category(description)
    recurrence_risk = "LOW"
    if clusters:
        risks = [c.get("recurrence_risk", "LOW") for c in clusters]
        if "HIGH" in risks:
            recurrence_risk = "HIGH"
        elif "MEDIUM" in risks:
            recurrence_risk = "MEDIUM"

    return {
        "root_cause_hypotheses": hypotheses,
        "ishikawa_categories": categories,
        "recurrence_risk": recurrence_risk,
        "investigation_method": "five-why / ishikawa (formal investigation required)",
        "similar_event_count": len(similar_events),
    }
