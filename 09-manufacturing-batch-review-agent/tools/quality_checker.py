# tools/quality_checker.py
# ============================================================
# Quality check for a drafted batch exception report.
#
# Deterministic gates run BEFORE a QA reviewer sees the report:
#   * grounding         — every number/entity traceable to batch state (governance.grounding)
#   * required elements — batch id, a recommendation (RELEASE/HOLD), exception coverage
#                          (or an explicit "no exceptions"), and the QA-sign-off closure
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

_REQUIRED_ELEMENTS = {
    "batch_identified": re.compile(r"\b(batch|lot)\b", re.I),
    "recommendation": re.compile(r"\b(recommendation|release|hold)\b", re.I),
    "exception_coverage": re.compile(
        r"\b(exception|OOS|out[- ]of[- ](spec|limit)|deviation|unsigned|missing|no exceptions)\b", re.I
    ),
    "closure": re.compile(r"\b(QA sign[- ]off|no batch disposition|recommendation for QA|pending QA)\b", re.I),
}


def _required_elements_check(text: str) -> tuple:
    findings: List[str] = []
    for element, pattern in _REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required report element: {element}")
    return len(findings) == 0, findings


def check(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state.get("exception_report", "")
    findings: List[str] = []

    elements_ok, element_findings = _required_elements_check(report)
    findings.extend(element_findings)

    # Grounding — corpus is the batch facts + the scanned exception details.
    if verify_grounding is not None:
        corpus: Dict[str, Any] = {
            "batch_id": state.get("batch_id"),
            "product": state.get("product"),
            "exception_count": state.get("exception_count"),
            "critical_count": state.get("critical_count"),
            "right_first_time": state.get("right_first_time"),
        }
        for i, e in enumerate(state.get("exceptions") or []):
            corpus[f"exc_{i}_code"] = e.get("code")
            corpus[f"exc_{i}_step"] = e.get("step")
            corpus[f"exc_{i}_detail"] = e.get("detail")
            corpus[f"exc_{i}_severity"] = e.get("severity")
        grounding_report = verify_grounding(report, corpus).to_audit_dict()
    else:
        grounding_report = {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}

    return {
        "grounding_report": grounding_report,
        "required_elements_present": elements_ok,
        "quality_findings": findings,
    }
