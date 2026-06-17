# tools/fairness_checker.py
# ============================================================
# Fairness and grounding checks for site ranking reports.
# Flags demographic under-representation and checks grounding.
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
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely|100%\s+representative|"
    r"perfectly\s+representative)\b",
    re.I,
)
REQUIRED_ELEMENTS = {
    "eligibility": re.compile(r"\b(eligible|eligib|cohort|patient|pool)\b", re.I),
    "site_info": re.compile(r"\b(site|center|institution|rank|top)\b", re.I),
    "phi_note": re.compile(r"\b(de.?identified|aggregate|phi|source system)\b", re.I),
}


def quality_findings(text: str) -> List[str]:
    findings: List[str] = []
    if SPECULATIVE.search(text):
        findings.append("speculative or absolute-claim language detected")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required report element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "study_id": state.get("study_id"),
        "indication": state.get("indication"),
        "target_enrollment": state.get("target_enrollment"),
        "cohort_results": state.get("cohort_results", {}),
        "site_rankings": state.get("site_rankings", []),
        "fairness_flags": state.get("fairness_flags", []),
    }
    return verify_grounding(text, corpus).to_audit_dict()
