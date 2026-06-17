"""
Deterministic core for the Clinical Trial Ops native rebuild.

All non-LLM logic lives here: TMF compliance gate, risk scoring,
query compilation, and routing. The LLM (strands_agent.py) only
DRAFTS the study health briefing; this module decides whether the
draft is clean, needs revision, or must escalate to a CTM.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# Speculative / non-GCP language patterns
PROHIBITED = re.compile(
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely|100%\s+(?:compliant|complete|enrolled)|"
    r"no\s+doubt|absolutely\s+safe)\b",
    re.I,
)

# Required briefing elements
REQUIRED = {
    "status":      re.compile(r"\b(enrollment|enroll(?:ed|ment)|status|study)\b", re.I),
    "data_quality": re.compile(r"\b(missing|deviation|query|CRF|data|flag)\b", re.I),
    "tmf":         re.compile(r"\b(eTMF|TMF|completeness|inspection)\b", re.I),
    "action":      re.compile(r"\b(recommend|action|clinical operations|lead|approved?)\b", re.I),
}

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")

# ICH E6(R2) critical TMF sections
_CRITICAL_TMF_KEYWORDS = {
    "irb correspondence", "irb approval", "informed consent",
    "investigator brochure", "regulatory approval", "randomization list",
}


def compliance_findings(text: str) -> List[str]:
    out: List[str] = []
    if PROHIBITED.search(text):
        out.append("prohibited speculative/absolute-claim language detected")
    for el, pat in REQUIRED.items():
        if not pat.search(text):
            out.append(f"missing required element: {el}")
    return out


def grounding_findings(text: str, evidence: Dict[str, Any]) -> List[str]:
    """Numbers >12 in text must appear in evidence values."""
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


def tmf_risk(missing_documents: List[str], completeness_pct: float) -> str:
    """Return CRITICAL / HIGH / MEDIUM / LOW based on TMF state."""
    for doc in missing_documents:
        for kw in _CRITICAL_TMF_KEYWORDS:
            if kw in doc.lower():
                return "CRITICAL"
    if completeness_pct < 75:
        return "CRITICAL"
    if completeness_pct < 90:
        return "HIGH"
    if completeness_pct < 95:
        return "MEDIUM"
    return "LOW"


def risk_score(enrolled: int, target: int, tmf_pct: float,
               tmf_critical: bool, query_rate: float) -> Dict[str, Any]:
    """Composite risk score 0-100 and tier."""
    e_score = 0 if enrolled / max(target, 1) >= 0.9 else \
              10 if enrolled / max(target, 1) >= 0.7 else \
              20 if enrolled / max(target, 1) >= 0.5 else 30
    t_score = 30 if tmf_critical else \
              30 if tmf_pct < 75 else 20 if tmf_pct < 90 else 10 if tmf_pct < 95 else 0
    q_score = 0 if query_rate <= 0.5 else 8 if query_rate <= 1.5 else 15 if query_rate <= 3 else 20
    composite = e_score + t_score + q_score
    tier = "CRITICAL" if composite >= 70 else "HIGH" if composite >= 45 else \
           "MEDIUM" if composite >= 20 else "LOW"
    return {"composite_score": composite, "risk_tier": tier,
            "component_scores": {"enrollment": e_score, "tmf": t_score, "queries": q_score}}


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
    tmf_data = evidence.get("tmf_data", {})
    missing_docs = tmf_data.get("missing_documents", [])
    tmf_pct = float(tmf_data.get("completeness_pct", 100))
    t_risk = tmf_risk(missing_docs, tmf_pct)
    rs = risk_score(
        enrolled=int(evidence.get("enrolled", 0)),
        target=int(evidence.get("target", 1)),
        tmf_pct=tmf_pct,
        tmf_critical=(t_risk == "CRITICAL"),
        query_rate=float(evidence.get("query_rate", 0)),
    )
    severe = any("prohibited" in c for c in comp) or t_risk == "CRITICAL" or rs["risk_tier"] == "CRITICAL"
    if severe:
        return {"next": "HumanReviewGate", "action": "ESCALATE",
                "compliance": comp, "grounding": grnd, "risk": rs, "tmf_risk": t_risk}
    if (comp or grnd) and revision_count < 1:
        return {"next": "Draft", "action": "REVISE",
                "compliance": comp, "grounding": grnd, "risk": rs, "tmf_risk": t_risk}
    return {"next": "HumanReviewGate", "action": "APPROVE_BRIEF",
            "compliance": comp, "grounding": grnd, "risk": rs, "tmf_risk": t_risk}
