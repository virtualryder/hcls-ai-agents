"""
Deterministic core for the native Protocol Design rebuild.

All non-LLM logic lives here: guidance relevance scoring, feasibility assessment,
regulatory risk detection, the compliance/grounding gate, and the routing decision.
The LLM (strands_agent.py) only DRAFTS protocol sections; this module decides
whether a draft is complete, needs revision, or must escalate for regulatory review.
No AWS, no model — unit-testable in demo mode.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# ── Required protocol section elements ────────────────────────────────────────
REQUIRED = {
    "endpoint": re.compile(r"\b(endpoint|primary|secondary|outcome|measure)\b", re.I),
    "eligibility": re.compile(r"\b(inclusion|exclusion|eligib|criteria|population)\b", re.I),
    "schedule": re.compile(r"\b(schedule|visit|screening|follow.?up|timepoint)\b", re.I),
    "reviewer_note": re.compile(r"\b(review|approved?|medical|clinical|human)\b", re.I),
}

# ── Speculative / absolute language ──────────────────────────────────────────
SPECULATIVE = re.compile(
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely\s+effective|"
    r"100%\s+(?:safe|effective|successful))\b", re.I
)

# ── Regulatory risk patterns ──────────────────────────────────────────────────
_SPECIAL_POP = re.compile(
    r"\b(pediatric|children|neonate|elderly|pregnant|immunocompromised)\b", re.I
)
_SURROGATE = re.compile(r"\b(surrogate|pfs|progression[- ]free|biomarker[- ]endpoint)\b", re.I)
_NOVEL_DESIGN = re.compile(r"\b(adaptive|basket|platform|seamless|bayesian)\b", re.I)

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")


def compliance_findings(text: str) -> List[str]:
    """Check protocol draft for required elements and speculative language."""
    out: List[str] = []
    if SPECULATIVE.search(text):
        out.append("speculative efficacy/safety claims detected — remove absolute language")
    for el, pat in REQUIRED.items():
        if not pat.search(text):
            out.append(f"missing required protocol element: {el}")
    return out


def regulatory_risks(state: Dict[str, Any]) -> List[str]:
    """Detect regulatory risks from protocol design parameters."""
    risks: List[str] = []
    objective = state.get("primary_objective", "")
    population = state.get("target_population", "")
    design = state.get("study_design", "")
    phase = state.get("phase", "")
    draft = state.get("draft_protocol", "")
    guidance = state.get("guidance_hits", [])

    if not guidance:
        risks.append(
            "No regulatory guidance identified — consult regulatory affairs before finalizing."
        )
    if _SPECIAL_POP.search(population) or _SPECIAL_POP.search(draft):
        risks.append(
            "Special population (pediatric, elderly, or vulnerable group) — additional regulatory consultation required."
        )
    if _SURROGATE.search(objective) and phase in ("Phase 3", "Phase 2/3"):
        risks.append(
            "Surrogate endpoint proposed for late-stage trial — confirm regulatory acceptability."
        )
    if _NOVEL_DESIGN.search(design) or _NOVEL_DESIGN.search(draft):
        risks.append(
            "Novel or complex design — early regulatory interaction strongly recommended."
        )
    return risks


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
          state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Determine next step: REVISE (loop back to Draft), or HumanReviewGate.
    ESCALATE if high regulatory risk and quality findings remain.
    """
    state = state or {}
    comp = compliance_findings(draft)
    grnd = grounding_findings(draft, evidence)
    reg = regulatory_risks({**state, "draft_protocol": draft})

    escalate = bool(reg) and bool(comp)
    if escalate:
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "compliance": comp,
            "grounding": grnd,
            "regulatory_risks": reg,
        }
    if (comp or grnd) and revision_count < 1:
        return {
            "next": "Draft",
            "action": "REVISE",
            "compliance": comp,
            "grounding": grnd,
            "regulatory_risks": reg,
        }
    return {
        "next": "HumanReviewGate",
        "action": "APPROVE_DRAFT",
        "compliance": comp,
        "grounding": grnd,
        "regulatory_risks": reg,
    }
