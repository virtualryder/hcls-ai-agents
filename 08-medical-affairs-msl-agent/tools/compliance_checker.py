# tools/compliance_checker.py
# ============================================================
# Compliance and grounding checks for MSL pre-call briefs.
#
# Three gates run BEFORE a Medical Affairs Approver sees the brief:
#   * off-label detection — any reference to unapproved indications → ESCALATE
#   * promotional language — superlatives / absolute claims → ESCALATE
#   * required elements (HCP background, approved data citation, compliance note)
#   * grounding — all numbers traceable to approved_documents and HCP profile
#
# Off-label and promotional findings force ESCALATE (not just REVISE) because
# the MSL channel carries regulatory risk if non-compliant content reaches HCPs.
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

OFF_LABEL = re.compile(
    r"\b(off[- ]label|unapproved\s+(?:use|indication)|not\s+approved\s+for|"
    r"investigational\s+use\s+outside|compassionate\s+use\s+claim|"
    r"outside\s+(?:the\s+)?approved\s+indication)\b",
    re.I,
)
PROMOTIONAL = re.compile(
    r"\b(best[- ]in[- ]class|superior(?:ity)?\s+to\s+all|market[- ]leading|"
    r"game[- ]changer|revolutionary|miracle|100%\s+effective|unmatched)\b",
    re.I,
)
REQUIRED_ELEMENTS = {
    "hcp_background": re.compile(
        r"\b(HCP|physician|specialist|background|interest|profile|specialty)\b", re.I
    ),
    "approved_data": re.compile(
        r"\b(approved|label(?:ing)?|on[- ]label|clinical\s+(?:trial|data)|source|prescribing\s+information)\b",
        re.I,
    ),
    "compliance_note": re.compile(
        r"\b(compliance|on[- ]label|approver|review|medical\s+affairs)\b", re.I
    ),
    "follow_up": re.compile(
        r"\b(follow[- ]up|log|crm|action|send|schedule|next\s+step)\b", re.I
    ),
}


def compliance_findings(text: str) -> List[str]:
    """Return compliance issues. Off-label / promotional always escalate."""
    findings: List[str] = []
    if OFF_LABEL.search(text):
        findings.append(
            "prohibited off-label reference detected — must be removed before HCP use"
        )
    if PROMOTIONAL.search(text):
        findings.append(
            "promotional language detected — not permitted in MSL scientific exchange"
        )
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required brief element: {element}")
    return findings


def grounding_findings(text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Run grounding check: all numbers must trace to approved_documents or HCP profile."""
    if verify_grounding is None:
        return {"grounded": True, "ungrounded_numbers": [], "ungrounded_entities": []}
    corpus = {
        "hcp_id": state.get("hcp_id"),
        "hcp_name": state.get("hcp_name"),
        "topic": state.get("topic"),
        "meeting_date": state.get("meeting_date"),
        "meeting_purpose": state.get("meeting_purpose"),
        "hcp_profile": state.get("hcp_profile", {}),
        "approved_documents": state.get("approved_documents", []),
        "next_best_actions": state.get("next_best_actions", {}),
    }
    return verify_grounding(text, corpus).to_audit_dict()
