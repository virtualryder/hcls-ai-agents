"""
Deterministic core for the Site Patient Matching native rebuild.

All non-LLM logic: eligibility translation, cohort feasibility scoring,
fairness checks, compliance gating, and routing.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

PROHIBITED = re.compile(
    r"\b(guarantee[sd]?|certain(?:ly)?|definitely|100%\s+representative|"
    r"perfectly\s+representative)\b",
    re.I,
)

REQUIRED = {
    "eligibility": re.compile(r"\b(eligible|cohort|patient|pool)\b", re.I),
    "site_info":   re.compile(r"\b(site|center|rank|top)\b", re.I),
    "phi_note":    re.compile(r"\b(de.?identified|aggregate|phi|source system)\b", re.I),
    "action":      re.compile(r"\b(recommend|action|review|approved?|outreach)\b", re.I),
}

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
_BLACK_BENCHMARK = 13
_HISPANIC_BENCHMARK = 18


def compliance_findings(text: str) -> List[str]:
    out: List[str] = []
    if PROHIBITED.search(text):
        out.append("prohibited speculative/absolute-claim language detected")
    for el, pat in REQUIRED.items():
        if not pat.search(text):
            out.append(f"missing required element: {el}")
    return out


def grounding_findings(text: str, evidence: Dict[str, Any]) -> List[str]:
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


def fairness_flags(site_counts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    for site in site_counts:
        demo = site.get("demographics", {})
        if demo.get("pct_black", 100) < _BLACK_BENCHMARK:
            flags.append({
                "site_id": site.get("site_id", "UNKNOWN"),
                "demographic": "Black/African American",
                "site_pct": demo.get("pct_black", 0),
                "benchmark_pct": _BLACK_BENCHMARK,
                "severity": "MODERATE",
            })
    return flags


def feasibility_score(
    total_eligible: int,
    target_enrollment: int,
    n_sites: int,
    n_equity_flags: int,
) -> Dict[str, Any]:
    coverage = total_eligible / max(target_enrollment, 1)
    if coverage >= 5:
        pool_score = 100
    elif coverage >= 3:
        pool_score = 75
    elif coverage >= 1.5:
        pool_score = 50
    else:
        pool_score = 25
    site_score = min(n_sites * 15, 100)
    equity_penalty = n_equity_flags * 10
    composite = max(0, min(100, int((pool_score + site_score) / 2 - equity_penalty)))
    tier = "HIGH" if composite >= 70 else "MEDIUM" if composite >= 40 else "LOW"
    return {"composite": composite, "tier": tier,
            "pool_score": pool_score, "site_score": site_score,
            "equity_penalty": equity_penalty}


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
    site_counts = evidence.get("cohort_results", {}).get("site_counts", [])
    flags = fairness_flags(site_counts)
    score = feasibility_score(
        total_eligible=int(evidence.get("cohort_results", {}).get("total_eligible", 0)),
        target_enrollment=int(evidence.get("target_enrollment", 1)),
        n_sites=len(site_counts),
        n_equity_flags=len([f for f in flags if f["severity"] == "CRITICAL"]),
    )
    critical_equity = any(f["severity"] == "CRITICAL" for f in flags)
    severe = any("prohibited" in c for c in comp) or critical_equity
    if severe:
        return {"next": "HumanReviewGate", "action": "ESCALATE",
                "compliance": comp, "grounding": grnd,
                "fairness_flags": flags, "feasibility": score}
    if (comp or grnd) and revision_count < 1:
        return {"next": "Draft", "action": "REVISE",
                "compliance": comp, "grounding": grnd,
                "fairness_flags": flags, "feasibility": score}
    return {"next": "HumanReviewGate", "action": "APPROVE_RANKING",
            "compliance": comp, "grounding": grnd,
            "fairness_flags": flags, "feasibility": score}
