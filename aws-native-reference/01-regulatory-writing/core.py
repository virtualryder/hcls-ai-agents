"""
Deterministic core for the native Regulatory Writing rebuild.

All non-LLM logic lives here so it can run in Lambdas, be unit-tested without a
model, and stay auditable: evidence assembly, the compliance gate, and the
grounding gate. The LLM (strands_agent.py) only DRAFTS; this module decides
whether a draft is clean, needs revision, or must escalate.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

PROHIBITED = re.compile(
    r"\b(cure[sd]?|guarantee[sd]?|miracle|100% effective|completely safe|no side effects|"
    r"best[- ]in[- ]class)\b", re.I,
)
REQUIRED = {
    "purpose": re.compile(r"\b(purpose|objective|scope|background|introduction)\b", re.I),
    "data": re.compile(r"\b(data|result|finding|study|analysis|evidence|endpoint)\b", re.I),
    "benefit_risk": re.compile(r"\b(benefit|risk|safety|efficacy|tolerab|favorable)\w*", re.I),
    "conclusion": re.compile(r"\b(conclu|therefore|in summary|overall|recommend|support)\w*", re.I),
}
_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")


def compliance_findings(text: str) -> List[str]:
    out: List[str] = []
    if PROHIBITED.search(text):
        out.append("prohibited promotional/off-label/absolute-claim language")
    for el, pat in REQUIRED.items():
        if not pat.search(text):
            out.append(f"missing required element: {el}")
    return out


def grounding_findings(text: str, evidence: Dict[str, Any]) -> List[str]:
    """Lightweight grounding: numbers >12 in text must appear in evidence values."""
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


def route(evidence: Dict[str, Any], draft: str, revision_count: int) -> Dict[str, Any]:
    comp = compliance_findings(draft)
    grnd = grounding_findings(draft, evidence)
    severe = any("prohibited" in c for c in comp)
    if severe:
        return {"next": "HumanReviewGate", "action": "ESCALATE", "compliance": comp, "grounding": grnd}
    if (comp or grnd) and revision_count < 1:
        return {"next": "Draft", "action": "REVISE", "compliance": comp, "grounding": grnd}
    return {"next": "HumanReviewGate", "action": "APPROVE_DRAFT", "compliance": comp, "grounding": grnd}
