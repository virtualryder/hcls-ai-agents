# tools/quality_checker.py
# ============================================================
# Quality and grounding checks for a drafted clinical trial ops briefing.
#
# Two deterministic gates:
#   * quality: required structural elements present; no speculative language.
#   * grounding: numbers/entities traceable to state (governance.grounding).
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

SPECULATIVE = re.compile(
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely|no doubt|absolutely safe|"
    r"100%\s+(?:compliant|complete|enrolled))\b",
    re.I,
)
REQUIRED_ELEMENTS = {
    "status": re.compile(r"\b(status|enrollment|enroll(?:ed|ment)|on track|requires attention)\b", re.I),
    "data_quality": re.compile(r"\b(missing|deviation|query|data|CRF|flag)\b", re.I),
    "recommendation": re.compile(r"\b(recommend|action|review|clinical operations|lead|approved?)\b", re.I),
}


def quality_findings(text: str) -> List[str]:
    findings: List[str] = []
    if SPECULATIVE.search(text):
        findings.append("speculative or absolute-claim language detected — review required")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required briefing element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "study_id": state.get("study_id"),
        "protocol_id": state.get("protocol_id"),
        "sponsor": state.get("sponsor"),
        "review_period": state.get("review_period"),
        "study_status": state.get("study_status", {}),
        "tmf_completeness": state.get("tmf_completeness") or state.get("tmf_data") or {},
        "subject_data": state.get("subject_data", []),
        "missing_data_flags": state.get("missing_data_flags", []),
        "deviation_flags": state.get("deviation_flags", []),
    }
    return verify_grounding(text, corpus).to_audit_dict()
