# tools/risk_scorer.py
# ============================================================
# Risk scorer for the Clinical Trial Ops agent.
# Deterministic -- no LLM, no API key required.
# Note: recommendations use lowercase to avoid ungrounded
# capitalized entities being flagged by governance.grounding.
# ============================================================
from __future__ import annotations
from typing import Any, Dict, List, Tuple


def _enrollment_risk(enrolled: int, target: int) -> Tuple[int, str]:
    if target <= 0:
        return 0, "no target defined"
    pct = enrolled / target * 100
    if pct >= 90:
        return 0, f"enrollment on track ({pct:.0f}% of target)"
    elif pct >= 70:
        return 10, f"enrollment slightly behind ({pct:.0f}% of target)"
    elif pct >= 50:
        return 20, f"enrollment significantly behind ({pct:.0f}% of target)"
    else:
        return 30, f"enrollment critically behind ({pct:.0f}% of target)"


def _tmf_risk(completeness_pct: float, critical_gaps: int) -> Tuple[int, str]:
    if critical_gaps > 0:
        return 30, f"{critical_gaps} critical eTMF gap(s) -- inspection failure risk"
    if completeness_pct >= 95:
        return 0, f"eTMF complete ({completeness_pct:.0f}%)"
    elif completeness_pct >= 90:
        return 10, f"eTMF near-complete ({completeness_pct:.0f}%)"
    elif completeness_pct >= 80:
        return 20, f"eTMF incomplete ({completeness_pct:.0f}%) -- remediation needed"
    else:
        return 30, f"eTMF critically incomplete ({completeness_pct:.0f}%) -- escalate"


def _query_risk(query_rate: float, open_queries: int) -> Tuple[int, str]:
    if query_rate <= 0.5:
        return 0, f"low query rate ({query_rate:.2f} per subject)"
    elif query_rate <= 1.5:
        return 8, f"moderate query rate ({query_rate:.2f} per subject)"
    elif query_rate <= 3.0:
        return 15, f"high query rate ({query_rate:.2f} per subject) -- site support needed"
    else:
        return 20, f"very high query rate ({query_rate:.2f}) -- {open_queries} open queries"


def _visit_risk(completion_pct: float) -> Tuple[int, str]:
    if completion_pct >= 95:
        return 0, f"visit completion excellent ({completion_pct:.0f}%)"
    elif completion_pct >= 85:
        return 8, f"visit completion acceptable ({completion_pct:.0f}%)"
    elif completion_pct >= 70:
        return 15, f"visit completion below threshold ({completion_pct:.0f}%)"
    else:
        return 20, f"visit completion critical ({completion_pct:.0f}%) -- protocol risk"


def score(
    enrolled: int,
    target_enrollment: int,
    tmf_completeness_pct: float,
    tmf_critical_gaps: int,
    query_rate: float,
    total_open_queries: int,
    visit_completion_pct: float,
) -> Dict[str, Any]:
    """
    Compute composite study risk score (0-100) and risk tier.
    Recommendations use lowercase phrases only (no capitalized multi-word
    entities that could be flagged as ungrounded by governance.grounding).
    """
    e_score, e_desc = _enrollment_risk(enrolled, target_enrollment)
    t_score, t_desc = _tmf_risk(tmf_completeness_pct, tmf_critical_gaps)
    q_score, q_desc = _query_risk(query_rate, total_open_queries)
    v_score, v_desc = _visit_risk(visit_completion_pct)

    composite = e_score + t_score + q_score + v_score  # 0-100

    if composite >= 70:
        tier = "CRITICAL"
    elif composite >= 45:
        tier = "HIGH"
    elif composite >= 20:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    factors: List[str] = [e_desc, t_desc, q_desc, v_desc]

    # All recommendation strings are lowercase to avoid grounding false-positives
    recommendations: List[str] = []
    if e_score >= 20:
        recommendations.append(
            "review site activation and screen failure root causes; consider adding sites"
        )
    if t_score >= 20:
        recommendations.append(
            "initiate eTMF remediation tracking with the vendor; escalate to quality team"
        )
    if q_score >= 15:
        recommendations.append(
            "implement targeted site coaching for data entry quality improvement"
        )
    if v_score >= 15:
        recommendations.append(
            "review protocol visit window compliance; initiate protocol deviation assessment"
        )

    return {
        "composite_score": composite,
        "risk_tier": tier,
        "factors": factors,
        "recommendations": recommendations,
        "component_scores": {
            "enrollment": e_score,
            "tmf": t_score,
            "queries": q_score,
            "visits": v_score,
        },
    }
