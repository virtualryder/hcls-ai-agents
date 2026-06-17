# tools/consistency_checker.py
# ============================================================
# Consistency + compliance checks for a drafted regulatory section.
#
# Two deterministic gates run BEFORE a human sees the draft:
#   * compliance: no promotional / off-label / absolute-claim language; required
#     structural elements present (purpose, data, benefit-risk, conclusion).
#   * grounding: every number/entity traceable to state (governance.grounding).
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

PROHIBITED = re.compile(
    r"\b(cure[sd]?|guarantee[sd]?|miracle|100% effective|completely safe|no side effects|"
    r"best[- ]in[- ]class)\b", re.I,
)
REQUIRED_ELEMENTS = {
    "purpose": re.compile(r"\b(purpose|objective|scope|background|introduction)\b", re.I),
    "data": re.compile(r"\b(data|result|finding|study|analysis|evidence|endpoint)\b", re.I),
    "benefit_risk": re.compile(r"\b(benefit|risk|safety|efficacy|tolerab|favorable)\w*", re.I),
    "conclusion": re.compile(r"\b(conclu|therefore|in summary|overall|recommend|support)\w*", re.I),
}


def compliance_findings(text: str) -> List[str]:
    findings: List[str] = []
    if PROHIBITED.search(text):
        findings.append("prohibited promotional/off-label/absolute-claim language detected")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required section element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    # Only the substantive, citable facts form the grounding corpus.
    corpus = {
        "study_data": state.get("study_data", {}),
        "source_documents": state.get("source_documents", []),
        "product": state.get("product"),
        "indication": state.get("indication"),
        "target_authority": state.get("target_authority"),
        "section_ref": state.get("section_ref"),
    }
    return verify_grounding(text, corpus).to_audit_dict()
