# tools/cohort_estimator.py
from __future__ import annotations
from typing import Any, Dict, List

_DEFAULT_SCREEN_ENROLL_RATIO = 3.0
_DEFAULT_MONTHLY_SCREEN_RATE = 0.04


def estimate_site(
    site_id: str,
    eligible_count: int,
    target_enrollment: int,
    study_duration_months: int = 24,
    screen_enroll_ratio: float = _DEFAULT_SCREEN_ENROLL_RATIO,
    monthly_screen_rate: float = _DEFAULT_MONTHLY_SCREEN_RATE,
) -> Dict[str, Any]:
    if eligible_count <= 0:
        return {
            "site_id": site_id,
            "eligible_count": 0,
            "projected_enrollees": 0,
            "months_to_target": None,
            "feasible": False,
            "recommendation": "de-prioritize: no eligible patients identified",
            "notes": ["eligible_count is 0 or negative"],
        }
    monthly_enrolled = (eligible_count * monthly_screen_rate) / screen_enroll_ratio
    months_to_target = (
        target_enrollment / monthly_enrolled if monthly_enrolled > 0 else None
    )
    projected_enrollees = int(monthly_enrolled * study_duration_months)
    feasible = (months_to_target is not None and months_to_target <= study_duration_months)
    if projected_enrollees >= target_enrollment:
        recommendation = "activate: projected to meet enrollment target independently"
    elif projected_enrollees >= int(target_enrollment * 0.5):
        recommendation = "activate with supplemental support: projected to contribute significantly"
    elif projected_enrollees >= int(target_enrollment * 0.2):
        recommendation = "activate as supplemental site: modest enrollment contribution expected"
    else:
        recommendation = "de-prioritize: insufficient eligible pool to justify activation cost"
    notes = []
    if months_to_target and months_to_target > study_duration_months:
        notes.append(
            f"projected months to target ({months_to_target:.0f}) exceeds study window ({study_duration_months})"
        )
    if eligible_count < 30:
        notes.append("small eligible pool; estimate has high uncertainty")
    return {
        "site_id": site_id,
        "eligible_count": eligible_count,
        "projected_enrollees": projected_enrollees,
        "months_to_target": round(months_to_target, 1) if months_to_target else None,
        "feasible": feasible,
        "recommendation": recommendation,
        "notes": notes,
    }


def estimate_portfolio(
    site_counts: List[Dict[str, Any]],
    target_enrollment: int,
    study_duration_months: int = 24,
    screen_enroll_ratio: float = _DEFAULT_SCREEN_ENROLL_RATIO,
    monthly_screen_rate: float = _DEFAULT_MONTHLY_SCREEN_RATE,
) -> Dict[str, Any]:
    estimates = []
    for s in site_counts:
        if not isinstance(s, dict):
            continue
        estimates.append(estimate_site(
            site_id=str(s.get("site_id", "UNKNOWN")),
            eligible_count=int(s.get("eligible_count", 0)),
            target_enrollment=target_enrollment,
            study_duration_months=study_duration_months,
            screen_enroll_ratio=screen_enroll_ratio,
            monthly_screen_rate=monthly_screen_rate,
        ))
    total_projected = sum(e["projected_enrollees"] for e in estimates)
    portfolio_feasible = total_projected >= target_enrollment
    shortfall = max(0, target_enrollment - total_projected)
    total_monthly = sum(
        (s.get("eligible_count", 0) * monthly_screen_rate) / screen_enroll_ratio
        for s in site_counts if isinstance(s, dict) and s.get("eligible_count", 0) > 0
    )
    portfolio_months = round(target_enrollment / total_monthly, 1) if total_monthly > 0 else None
    top_sites = [
        e["site_id"] for e in sorted(estimates, key=lambda x: x["projected_enrollees"], reverse=True)[:3]
    ]
    return {
        "sites": estimates,
        "total_projected_enrollees": total_projected,
        "target_enrollment": target_enrollment,
        "portfolio_feasible": portfolio_feasible,
        "months_to_target": portfolio_months,
        "shortfall": shortfall,
        "top_recommended_sites": top_sites,
        "study_duration_months": study_duration_months,
    }
