# tools/risk_assessor.py
# ============================================================
# Operational and regulatory risk assessor for the Protocol Design agent.
#
# Evaluates both operational risks (enrollment, site, data quality) and
# regulatory risks (missing guidance, unclear endpoints, population scope)
# from the assembled protocol design state.
# ============================================================
from __future__ import annotations

import re
from typing import Any, Dict, List

# Patterns for regulatory risk triggers
_HIGH_RISK_POPULATIONS = re.compile(
    r"\b(pediatric|children|neonate|elderly|pregnant|immunocompromised|"
    r"renal impairment|hepatic impairment)\b", re.I
)
_SURROGATE_ENDPOINT = re.compile(
    r"\b(biomarker|surrogate|pfs|progression[- ]free|response rate|overall response)\b", re.I
)
_NOVEL_DESIGN = re.compile(
    r"\b(adaptive|seamless|basket|umbrella|platform|master protocol|bayesian)\b", re.I
)
_RWD_ENDPOINT = re.compile(
    r"\b(real[- ]world|registry|electronic health|ehr|claims data)\b", re.I
)


def assess_regulatory_risks(state: Dict[str, Any]) -> List[str]:
    """Identify regulatory risks from protocol design state."""
    risks: List[str] = []

    guidance_hits = state.get("guidance_hits", [])
    objective = state.get("primary_objective", "")
    population = state.get("target_population", "")
    design = state.get("study_design", "")
    phase = state.get("phase", "")
    draft = state.get("draft_protocol", "")
    indication = state.get("indication", "")

    if not guidance_hits:
        risks.append(
            "No regulatory guidance documents identified for this indication/phase combination — "
            "consult regulatory affairs before finalizing endpoints."
        )

    if _HIGH_RISK_POPULATIONS.search(population) or _HIGH_RISK_POPULATIONS.search(draft):
        risks.append(
            "Special population identified (pediatric, elderly, or vulnerable group) — "
            "additional regulatory consultation required (ICH E11, FDA guidance)."
        )

    if _SURROGATE_ENDPOINT.search(objective) and phase in ("Phase 3", "Phase 2/3"):
        risks.append(
            "Surrogate or intermediate endpoint proposed for late-stage trial — "
            "confirm regulatory acceptability with health authority before IND/CTA submission."
        )

    if _NOVEL_DESIGN.search(design) or _NOVEL_DESIGN.search(draft):
        risks.append(
            "Novel or complex adaptive design identified — early regulatory interaction "
            "(pre-IND, Scientific Advice) strongly recommended."
        )

    if _RWD_ENDPOINT.search(draft) or _RWD_ENDPOINT.search(objective):
        risks.append(
            "Real-world data or registry endpoints proposed — apply FDA RWE Framework "
            "criteria and ensure data quality/representativeness documented."
        )

    return risks


def assess_operational_risks(state: Dict[str, Any]) -> List[str]:
    """Identify operational risks from cohort and feasibility data."""
    risks: List[str] = []

    cohort = state.get("cohort_estimate", {})
    total_eligible = cohort.get("total_eligible", 0)
    sites = cohort.get("sites_with_data", 0)
    feasibility = state.get("feasibility_assessment", {})

    if total_eligible and total_eligible < 500:
        risks.append(
            f"Limited eligible pool (estimated {total_eligible} patients) — "
            "enrollment feasibility risk; consider broadening eligibility or adding international sites."
        )

    if sites and sites < 5:
        risks.append(
            f"Only {sites} sites identified with historical data — "
            "site activation risk; initiate site feasibility assessments early."
        )

    feasibility_risks = feasibility.get("feasibility_risks", [])
    for r in feasibility_risks:
        if r not in risks:
            risks.append(r)

    study_refs = state.get("study_status_refs", [])
    if study_refs:
        completed = [s for s in study_refs if s.get("status") == "COMPLETED"]
        if completed:
            ref = completed[0]
            if ref.get("enrollment_months") and ref["enrollment_months"] > 24:
                risks.append(
                    f"Historical precedent study enrolled over {ref['enrollment_months']} months — "
                    "plan buffer in timeline and consider contingency site activation."
                )

    return risks


def summarize_risk_profile(
    operational_risks: List[str], regulatory_risks: List[str]
) -> str:
    """Produce a concise risk summary for the protocol state."""
    total = len(operational_risks) + len(regulatory_risks)
    if total == 0:
        return "No material operational or regulatory risks identified at this stage."
    level = "HIGH" if total >= 3 else "MEDIUM" if total >= 1 else "LOW"
    return (
        f"Overall risk level: {level}. "
        f"{len(operational_risks)} operational risk(s) and "
        f"{len(regulatory_risks)} regulatory risk(s) identified. "
        "Qualified medical/clinical reviewer to assess before protocol finalization."
    )
