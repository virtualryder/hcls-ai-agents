# tools/protocol_checker.py
# ============================================================
# Regulatory and grounding checks for protocol drafts.
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
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely\s+effective|"
    r"100%\s+(?:safe|effective|successful))\b",
    re.I,
)
REQUIRED_ELEMENTS = {
    "endpoint": re.compile(r"\b(endpoint|primary|secondary|outcome|measure)\b", re.I),
    "eligibility": re.compile(r"\b(inclusion|exclusion|eligib|criteria|population)\b", re.I),
    "schedule": re.compile(r"\b(schedule|visit|screening|follow.?up|timepoint)\b", re.I),
    "reviewer_note": re.compile(r"\b(review|approved?|medical|clinical|human)\b", re.I),
}


def quality_findings(text: str) -> List[str]:
    findings: List[str] = []
    if SPECULATIVE.search(text):
        findings.append("speculative efficacy/safety claims detected — remove absolute language")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required protocol element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "indication": state.get("indication"),
        "phase": state.get("phase"),
        "therapeutic_area": state.get("therapeutic_area"),
        "primary_objective": state.get("primary_objective"),
        "target_population": state.get("target_population"),
        "study_design": state.get("study_design"),
        "cohort_estimate": state.get("cohort_estimate", {}),
        "guidance_hits": state.get("guidance_hits", []),
    }
    return verify_grounding(text, corpus).to_audit_dict()
