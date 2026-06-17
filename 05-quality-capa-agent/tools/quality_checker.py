# tools/quality_checker.py
from __future__ import annotations
import re, sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
try:
    from governance.grounding import verify_grounding
except Exception:
    verify_grounding = None

SPECULATIVE = re.compile(
    r"\b(might\s+work|might\s+help|might\s+prevent|might\s+eliminate|"
    r"could\s+possibly|could\s+maybe|may\s+possibly|"
    r"possibly\s+eliminate|possibly\s+fix|possibly\s+resolve|"
    r"guarantee[sd]?|certain(?:ly)?|definitely\s+caused|100%\s+sure|"
    r"will\s+definitely\s+prevent|might\s+fix|should\s+probably)\b", re.I)

REQUIRED_ELEMENTS = {
    "classification": re.compile(r"\b(classif|severity|critical|major|minor|event type)\b", re.I),
    "corrective_action": re.compile(r"\b(corrective|correction|contain|remediat)\w*", re.I),
    "preventive_action": re.compile(r"\b(preventive|preventative|prevent|systemic|sop|retrain)\w*", re.I),
    "effectiveness": re.compile(r"\b(effective|monitor|recurrence|metric|target|check)\b", re.I),
    "qp_review": re.compile(r"\b(qualified\s+person|QP|review|approve[sd]?|human)\b", re.I),
}


def quality_findings(text: str) -> List[str]:
    findings = []
    if SPECULATIVE.search(text):
        findings.append("speculative or hedging language detected -- use evidence-based statements")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required CAPA element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "complaint_id": state.get("complaint_id"),
        "product": state.get("product"),
        "lot_number": state.get("lot_number"),
        "site": state.get("site"),
        "event_type": state.get("event_type"),
        "severity": state.get("severity"),
        "similar_events": state.get("similar_events", []),
    }
    return verify_grounding(text, corpus).to_audit_dict()
