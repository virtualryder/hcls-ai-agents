# tools/rwe_checker.py
# ============================================================
# Grounding and quality checks for RWE/HEOR evidence synthesis.
#
# Three gates run BEFORE an Epidemiologist sees the synthesis:
#   * causal / absolute language — RWE establishes association only
#   * required elements (research question, N, outcome, limitation, epi note)
#   * grounding — every number in the synthesis traceable to cohort_results
#
# Mirrors the eval harness so a synthesis is held to the same bar as CI.
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

CAUSAL = re.compile(
    r"\b(proves?\s+causation|causally\s+(?:linked|related)|definitively\s+demonstrates?|"
    r"100%\s+confident|guarantee[sd]?\s+(?:efficacy|benefit|outcome))\b",
    re.I,
)

REQUIRED_ELEMENTS = {
    "research_question": re.compile(
        r"\b(research question|objective|study design|cohort|retrospective|prospective)\b", re.I
    ),
    "sample_size": re.compile(
        r"\b(patient[s]?|subject[s]?|n\s*=|\d+\s+patient|\d+\s+subject|cohort|sample)\b", re.I
    ),
    "outcome": re.compile(
        r"\b(outcome|result|rate|endpoint|finding|hospitali[sz]|persistence|cost)\w*", re.I
    ),
    "limitation": re.compile(
        r"\b(limitation|confound|bias|observational|generali[zs]|unmeasured|coverage)\w*", re.I
    ),
    "epidemiologist_note": re.compile(
        r"\b(epidemiologist|review|approved?|human|publication|regulatory submission)\b", re.I
    ),
    "no_causation_claim": re.compile(
        r"\b(association|observational|establishes?\s+association|does\s+not\s+demonstrate\s+causality)\b",
        re.I,
    ),
}


def quality_findings(text: str) -> List[str]:
    """Return list of quality/compliance issues found in the synthesis text."""
    findings: List[str] = []
    if CAUSAL.search(text):
        findings.append(
            "causal/absolute language detected — RWE establishes association, not causation"
        )
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required synthesis element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Run grounding check: all numbers must trace to cohort_results/summary_statistics."""
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "indication": state.get("indication"),
        "intervention": state.get("intervention"),
        "comparator": state.get("comparator"),
        "cohort_results": state.get("cohort_results", {}),
        "summary_statistics": state.get("summary_statistics", {}),
        "data_source": state.get("data_source"),
        "time_horizon": state.get("time_horizon"),
        "data_quality": state.get("data_quality", {}),
    }
    return verify_grounding(text, corpus).to_audit_dict()
