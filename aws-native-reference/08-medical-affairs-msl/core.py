"""
Deterministic core for the Medical Affairs MSL native rebuild.

All non-LLM logic lives here: document validation, compliance gate (off-label,
promotional), grounding check, and routing. The LLM (strands_agent.py) only
drafts the brief; this module decides clean/revise/escalate.

Key domain rules:
  * off-label language always escalates — never just revises
  * promotional language always escalates
  * numbers > 12 must appear in approved_documents corpus
  * missing required brief elements trigger REVISE (once)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
OFF_LABEL = re.compile(
    r"\b(off[- ]label|unapproved\s+(?:use|indication)|not\s+approved\s+for|"
    r"investigational\s+use\s+outside)\b",
    re.I,
)
PROMOTIONAL = re.compile(
    r"\b(best[- ]in[- ]class|superior(?:ity)?\s+to\s+all|market[- ]leading|"
    r"game[- ]changer|revolutionary|miracle|100%\s+effective)\b",
    re.I,
)
REQUIRED_ELEMENTS = {
    "hcp_background": re.compile(
        r"\b(HCP|physician|specialist|background|interest|profile|specialty)\b", re.I
    ),
    "approved_data": re.compile(
        r"\b(approved|label(?:ing)?|on[- ]label|clinical\s+(?:trial|data)|source)\b", re.I
    ),
    "compliance_note": re.compile(
        r"\b(compliance|on[- ]label|approver|review|medical\s+affairs)\b", re.I
    ),
}


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


def compliance_findings(text: str) -> List[str]:
    findings: List[str] = []
    if OFF_LABEL.search(text):
        findings.append("prohibited off-label reference detected — must escalate")
    if PROMOTIONAL.search(text):
        findings.append("promotional language detected — must escalate")
    for element, pattern in REQUIRED_ELEMENTS.items():
        if not pattern.search(text):
            findings.append(f"missing required brief element: {element}")
    return findings


def grounding_findings(text: str, approved_docs: List[Dict[str, Any]]) -> List[str]:
    """Numbers > 12 in the brief must appear in approved document texts."""
    corpus_parts: List[str] = []
    for doc in approved_docs:
        corpus_parts.append(str(doc.get("text", "")))
        corpus_parts.append(str(doc.get("title", "")))
        corpus_parts.append(str(doc.get("version", "")))
    corpus = " ".join(corpus_parts)
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


def route(
    text: str,
    approved_docs: List[Dict[str, Any]],
    revision_count: int,
) -> Dict[str, Any]:
    """
    Returns:
        {next: "Draft"|"HumanReviewGate", action: "REVISE"|"ESCALATE"|"APPROVE_BRIEF",
         compliance: [...], grounding: [...]}
    """
    comp = compliance_findings(text)
    grnd = grounding_findings(text, approved_docs)

    # Off-label or promotional always escalates (goes to human gate, not re-draft)
    severe = any(
        "off-label" in c or "promotional" in c for c in comp
    )
    if severe:
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "compliance": comp,
            "grounding": grnd,
        }
    if (comp or grnd) and revision_count < 1:
        return {
            "next": "Draft",
            "action": "REVISE",
            "compliance": comp,
            "grounding": grnd,
        }
    return {
        "next": "HumanReviewGate",
        "action": "APPROVE_BRIEF",
        "compliance": comp,
        "grounding": grnd,
    }
