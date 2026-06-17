"""
Deterministic core for the native Quality CAPA rebuild.

All non-LLM logic lives here: event classification, similarity clustering,
root-cause heuristics, the compliance/grounding gate, and the routing decision.
The LLM (strands_agent.py) only DRAFTS the CAPA plan text; this module decides
whether a draft is complete, needs revision, or must escalate to senior QP.
No AWS, no model — unit-testable in demo mode.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# ── Severity / risk classification ────────────────────────────────────────────
_CRITICAL_KW = re.compile(
    r"\b(death|fatal|life[- ]threatening|serious[- ]injury|recall|patient[- ]harm|"
    r"sterility|class[- ]i)\b", re.I
)
_MAJOR_KW = re.compile(
    r"\b(particulate|contamination|oos|out[- ]of[- ]spec|temperature[- ]excursion|"
    r"mislabel|equipment[- ]failure|deviation)\b", re.I
)

# ── Required CAPA plan elements ───────────────────────────────────────────────
REQUIRED = {
    "corrective_action": re.compile(r"\b(corrective|correction|contain|remediat)\w*", re.I),
    "preventive_action": re.compile(r"\b(preventive|preventative|prevent|systemic|sop)\w*", re.I),
    "effectiveness": re.compile(r"\b(effective|monitor|recurrence|metric|target|check)\b", re.I),
    "qp_review": re.compile(r"\b(qualified person|QP|review|approv)\w*", re.I),
}

# ── Speculative language ──────────────────────────────────────────────────────
SPECULATIVE = re.compile(
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely\s+caused|100%\s+sure|"
    r"will\s+definitely\s+prevent)\b", re.I
)

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")


def classify_event(description: str, declared_severity: str = "") -> Dict[str, Any]:
    """Classify a quality event and return severity and risk level."""
    desc = description or ""
    if declared_severity in ("CRITICAL", "MAJOR", "MINOR"):
        severity = declared_severity
    elif _CRITICAL_KW.search(desc):
        severity = "CRITICAL"
    elif _MAJOR_KW.search(desc):
        severity = "MAJOR"
    else:
        severity = "MINOR"

    risk_level = {"CRITICAL": "HIGH", "MAJOR": "MEDIUM", "MINOR": "LOW"}.get(severity, "LOW")
    return {"severity": severity, "risk_level": risk_level}


def compliance_findings(text: str) -> List[str]:
    """Check a CAPA plan for required elements and speculative language."""
    out: List[str] = []
    if SPECULATIVE.search(text):
        out.append("speculative causal language — use hypotheses, not conclusions")
    for el, pat in REQUIRED.items():
        if not pat.search(text):
            out.append(f"missing required CAPA element: {el}")
    return out


def grounding_findings(text: str, evidence: Dict[str, Any]) -> List[str]:
    """Numbers > 12 in text must appear in evidence values."""
    corpus = " ".join(str(v) for v in _flatten(evidence))
    corpus_nums = set(_NUM.findall(corpus))
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


def route(evidence: Dict[str, Any], draft: str, revision_count: int,
          risk_level: str = "MEDIUM") -> Dict[str, Any]:
    """
    Determine next step: REVISE (loop back to Draft), or HumanReviewGate.
    ESCALATE if risk=HIGH and regulatory obligation detected.
    """
    comp = compliance_findings(draft)
    grnd = grounding_findings(draft, evidence)
    reg_obligation = "regulatory" in draft.lower() or "reporting" in draft.lower()
    escalate = risk_level == "HIGH" and reg_obligation and any("qp_review" not in c for c in comp)
    if escalate and comp:
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "compliance": comp,
            "grounding": grnd,
        }
    if (comp or grnd) and revision_count < 1:
        return {"next": "Draft", "action": "REVISE", "compliance": comp, "grounding": grnd}
    return {
        "next": "HumanReviewGate",
        "action": "APPROVE_CAPA",
        "compliance": comp,
        "grounding": grnd,
    }
