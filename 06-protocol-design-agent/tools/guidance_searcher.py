# tools/guidance_searcher.py
# ============================================================
# Regulatory guidance search tool for the Protocol Design agent.
#
# In live mode, delegates to rim.search_guidance via the gateway.
# In demo mode, returns a curated fixture of ICH / FDA / EMA guidance
# documents relevant to common therapeutic areas and trial phases.
# ============================================================
from __future__ import annotations

import re
from typing import Any, Dict, List

# Curated demo guidance database
_GUIDANCE_DB: List[Dict[str, Any]] = [
    # ICH
    {
        "ref": "ICH E6(R2)",
        "title": "Good Clinical Practice: Integrated Addendum",
        "relevance_areas": ["all", "gcp", "informed consent", "monitoring"],
        "agency": "ICH",
        "topics": ["gcp", "protocol", "monitoring", "safety"],
    },
    {
        "ref": "ICH E9(R1)",
        "title": "Statistical Principles for Clinical Trials — Estimands",
        "relevance_areas": ["all", "endpoint", "estimand", "statistics", "primary endpoint"],
        "agency": "ICH",
        "topics": ["endpoint", "estimand", "randomization", "statistics"],
    },
    {
        "ref": "ICH E8(R1)",
        "title": "General Considerations for Clinical Studies",
        "relevance_areas": ["all", "study design", "protocol", "phase 1", "phase 2", "phase 3"],
        "agency": "ICH",
        "topics": ["study design", "protocol", "eligibility", "endpoints"],
    },
    {
        "ref": "ICH E11",
        "title": "Clinical Investigation of Medicinal Products in the Pediatric Population",
        "relevance_areas": ["pediatric", "children", "age", "paediatric"],
        "agency": "ICH",
        "topics": ["pediatric", "eligibility", "dosing"],
    },
    # FDA Oncology
    {
        "ref": "FDA-2018-ONCOLOGY-DOSE",
        "title": "FDA Guidance: Dose Optimization for Oncology Drugs",
        "relevance_areas": ["oncology", "cancer", "tumor", "dose", "phase 1"],
        "agency": "FDA",
        "topics": ["oncology", "dose", "phase 1", "safety"],
    },
    {
        "ref": "FDA-2018-MASTER-PROTOCOL",
        "title": "FDA Guidance: Master Protocols — Basket, Umbrella, and Platform Trials",
        "relevance_areas": ["oncology", "basket", "platform", "master protocol", "biomarker"],
        "agency": "FDA",
        "topics": ["oncology", "study design", "biomarker", "platform"],
    },
    {
        "ref": "FDA-2020-PRO",
        "title": "FDA Guidance: Patient-Reported Outcome Measures",
        "relevance_areas": ["patient-reported", "pro", "quality of life", "outcome", "endpoint"],
        "agency": "FDA",
        "topics": ["endpoint", "patient-reported", "quality of life"],
    },
    {
        "ref": "FDA-2019-ADAPT",
        "title": "FDA Guidance: Adaptive Designs for Clinical Trials of Drugs and Biologics",
        "relevance_areas": ["adaptive", "design", "interim analysis", "seamless", "randomization"],
        "agency": "FDA",
        "topics": ["study design", "adaptive", "statistics"],
    },
    # Cardiovascular
    {
        "ref": "FDA-2008-CV-ENDPOINTS",
        "title": "FDA Guidance: Evaluating Cardiovascular Risk in Drug Development",
        "relevance_areas": ["cardiovascular", "cardiac", "heart", "mace", "safety"],
        "agency": "FDA",
        "topics": ["cardiovascular", "safety", "endpoint", "mace"],
    },
    # RWD/RWE
    {
        "ref": "FDA-2021-RWE-FRAMEWORK",
        "title": "FDA Framework for Real-World Evidence Program",
        "relevance_areas": ["real-world", "rwe", "rwd", "registry", "electronic health records"],
        "agency": "FDA",
        "topics": ["rwd", "rwe", "feasibility", "registry"],
    },
    # EMA
    {
        "ref": "EMA-2016-ADAPTIVE",
        "title": "EMA Reflection Paper on Adaptive Designs",
        "relevance_areas": ["adaptive", "ema", "europe", "interim analysis"],
        "agency": "EMA",
        "topics": ["study design", "adaptive", "statistics"],
    },
]


def _score(doc: Dict[str, Any], query: str) -> float:
    """Score a guidance document against a free-text query."""
    query_lower = query.lower()
    score = 0.0
    # Match relevance areas
    for area in doc.get("relevance_areas", []):
        if area in query_lower or area == "all":
            score += 1.0
    # Match topics
    for topic in doc.get("topics", []):
        if topic in query_lower:
            score += 0.5
    return score


def search_guidance_demo(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Demo guidance search. Returns top-k documents by keyword relevance.
    All returned documents are from the curated fixture; no invented values.
    """
    scored = [(doc, _score(doc, query)) for doc in _GUIDANCE_DB]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for doc, score in scored[:top_k]:
        if score > 0:
            results.append({
                "ref": doc["ref"],
                "title": doc["title"],
                "agency": doc["agency"],
                "relevance_score": round(score, 2),
                "topics": doc["topics"],
            })
    # Always return at least the most broadly applicable guidance
    if not results:
        results = [
            {
                "ref": "ICH E6(R2)",
                "title": "Good Clinical Practice: Integrated Addendum",
                "agency": "ICH",
                "relevance_score": 0.5,
                "topics": ["gcp", "protocol"],
            },
            {
                "ref": "ICH E8(R1)",
                "title": "General Considerations for Clinical Studies",
                "agency": "ICH",
                "relevance_score": 0.5,
                "topics": ["study design", "protocol"],
            },
        ]
    return results


def format_guidance_summary(hits: List[Dict[str, Any]]) -> str:
    """Format guidance hits as a readable summary for prompts."""
    if not hits:
        return "No regulatory guidance documents identified."
    lines = ["Applicable regulatory guidance:"]
    for h in hits:
        lines.append(f"- {h['ref']}: {h['title']} ({h['agency']})")
    return "\n".join(lines)
