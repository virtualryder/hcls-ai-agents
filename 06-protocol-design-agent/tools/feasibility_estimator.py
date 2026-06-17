# tools/feasibility_estimator.py
# ============================================================
# Feasibility estimator for the Protocol Design agent.
#
# Estimates enrollment feasibility from RWD (real-world data)
# cohort query results and historical study precedent from CTMS.
# In demo mode returns structured fixture data — all numbers come
# from the fixture; none are invented by the model.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List

# Demo RWD cohort fixtures — indexed by indication keyword
_COHORT_FIXTURES: Dict[str, Dict[str, Any]] = {
    "nsclc": {
        "indication": "non-small cell lung cancer",
        "phase": "Phase 2",
        "total_eligible": 3240,
        "screened_12m": 890,
        "regions": ["Northeast US", "Southeast US", "Midwest US"],
        "sites_with_data": 14,
        "median_age_years": 67,
        "male_pct": 54,
        "icd10_codes": ["C34.10", "C34.11", "C34.12"],
        "phi_note": "Aggregate de-identified counts only per HIPAA Safe Harbor.",
    },
    "type 2 diabetes": {
        "indication": "type 2 diabetes mellitus",
        "phase": "Phase 3",
        "total_eligible": 18400,
        "screened_12m": 4200,
        "regions": ["Northeast US", "Southwest US", "Europe"],
        "sites_with_data": 31,
        "median_age_years": 59,
        "male_pct": 48,
        "icd10_codes": ["E11"],
        "phi_note": "Aggregate de-identified counts only per HIPAA Safe Harbor.",
    },
    "heart failure": {
        "indication": "heart failure with reduced ejection fraction",
        "phase": "Phase 3",
        "total_eligible": 5100,
        "screened_12m": 1300,
        "regions": ["Northeast US", "Midwest US", "Western EU"],
        "sites_with_data": 22,
        "median_age_years": 65,
        "male_pct": 61,
        "icd10_codes": ["I50.20", "I50.22"],
        "phi_note": "Aggregate de-identified counts only per HIPAA Safe Harbor.",
    },
    "default": {
        "indication": "general indication",
        "phase": "Phase 2",
        "total_eligible": 1200,
        "screened_12m": 320,
        "regions": ["US", "Europe"],
        "sites_with_data": 8,
        "median_age_years": 58,
        "male_pct": 50,
        "icd10_codes": [],
        "phi_note": "Aggregate de-identified counts only per HIPAA Safe Harbor.",
    },
}

# Historical study status fixtures
_STUDY_FIXTURES: List[Dict[str, Any]] = [
    {
        "study_id": "STUDY-PREC-001",
        "indication": "non-small cell lung cancer",
        "phase": "Phase 2",
        "design": "Single-arm",
        "enrollment_target": 120,
        "actual_enrolled": 118,
        "enrollment_months": 18,
        "sites": 12,
        "status": "COMPLETED",
        "primary_endpoint": "overall response rate",
    },
    {
        "study_id": "STUDY-PREC-002",
        "indication": "type 2 diabetes mellitus",
        "phase": "Phase 3",
        "design": "Randomized Controlled Trial",
        "enrollment_target": 600,
        "actual_enrolled": 612,
        "enrollment_months": 24,
        "sites": 28,
        "status": "COMPLETED",
        "primary_endpoint": "HbA1c reduction at 24 weeks",
    },
    {
        "study_id": "STUDY-PREC-003",
        "indication": "heart failure",
        "phase": "Phase 3",
        "design": "Randomized Controlled Trial",
        "enrollment_target": 500,
        "actual_enrolled": 492,
        "enrollment_months": 30,
        "sites": 20,
        "status": "COMPLETED",
        "primary_endpoint": "MACE composite endpoint",
    },
]


def _match_fixture(indication: str) -> Dict[str, Any]:
    """Select the most relevant cohort fixture by indication keyword."""
    ind_lower = (indication or "").lower()
    for key, fixture in _COHORT_FIXTURES.items():
        if key == "default":
            continue
        if any(word in ind_lower for word in key.split()):
            return dict(fixture)
    return dict(_COHORT_FIXTURES["default"])


def estimate_cohort_demo(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Demo cohort estimation. Returns fixture data matched by indication.
    All numbers sourced from fixture; no invented values.
    """
    indication = query.get("indication", "")
    cohort = _match_fixture(indication)
    # Overlay query indication for exact match in grounding
    cohort["query_indication"] = indication
    return cohort


def get_study_precedents_demo(indication: str, phase: str) -> List[Dict[str, Any]]:
    """Return historical study precedents matching indication and phase."""
    ind_lower = (indication or "").lower()
    phase_lower = (phase or "").lower()
    matched = [
        s for s in _STUDY_FIXTURES
        if any(word in s["indication"].lower() for word in ind_lower.split() if len(word) > 3)
        or phase_lower in s["phase"].lower()
    ]
    return matched or _STUDY_FIXTURES[:1]


def assess_feasibility(cohort: Dict[str, Any], enrollment_target: int = 200) -> Dict[str, Any]:
    """
    Assess enrollment feasibility from cohort data.
    Returns a structured feasibility assessment dict with risk flags.
    """
    total_eligible = cohort.get("total_eligible", 0)
    sites = cohort.get("sites_with_data", 1)
    screened_12m = cohort.get("screened_12m", 0)

    # Estimate enrollment rate (patients per site per month)
    enrollment_per_site_per_month = screened_12m / (sites * 12) if sites > 0 else 0
    months_to_enroll = (
        enrollment_target / (enrollment_per_site_per_month * sites)
        if enrollment_per_site_per_month > 0
        else None
    )

    risks: List[str] = []
    if total_eligible < enrollment_target * 2:
        risks.append(
            f"Eligible pool ({total_eligible}) is less than 2x enrollment target "
            f"({enrollment_target}) — consider broadening eligibility criteria."
        )
    if sites < 10:
        risks.append(
            f"Only {sites} sites have historical data — consider adding sites "
            "to meet enrollment timelines."
        )
    if months_to_enroll and months_to_enroll > 36:
        risks.append(
            f"Projected enrollment duration ({round(months_to_enroll)} months) "
            "exceeds 36 months — consider adaptive enrollment strategies."
        )

    return {
        "total_eligible": total_eligible,
        "sites_with_data": sites,
        "enrollment_per_site_per_month": round(enrollment_per_site_per_month, 2),
        "estimated_months_to_enroll": round(months_to_enroll) if months_to_enroll else None,
        "feasibility_risks": risks,
        "feasibility_rating": "LOW" if risks else "ACCEPTABLE",
        "phi_note": cohort.get("phi_note", "Aggregate de-identified counts only."),
    }
