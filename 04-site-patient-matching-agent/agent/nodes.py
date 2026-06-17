# agent/nodes.py
# ============================================================
# Node functions for the Site Patient Matching workflow.
#
# Workflow:
#   intake -> translate_criteria -> run_cohort_query ->
#   estimate_cohorts -> rank_sites -> fairness_review ->
#   [routing] -> human_review_gate -> finalize -> END
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, SitePatientMatchingState
from tools import gateway_tools, site_ranker, fairness_checker, eligibility_translator, cohort_estimator

_DEMO_COHORT_RESULTS: Dict[str, Any] = {
    "query_id": "DEMO-Q-001",
    "total_eligible": 1847,
    "sites_with_data": 6,
    "site_counts": [
        {"site_id": "SITE-NE-01", "region": "Northeast", "eligible_count": 423,
         "demographics": {"pct_female": 52, "pct_hispanic": 18, "pct_black": 14}},
        {"site_id": "SITE-SE-01", "region": "Southeast", "eligible_count": 387,
         "demographics": {"pct_female": 49, "pct_hispanic": 22, "pct_black": 28}},
        {"site_id": "SITE-MW-01", "region": "Midwest", "eligible_count": 312,
         "demographics": {"pct_female": 48, "pct_hispanic": 9, "pct_black": 11}},
        {"site_id": "SITE-W-01", "region": "West", "eligible_count": 298,
         "demographics": {"pct_female": 51, "pct_hispanic": 31, "pct_black": 8}},
        {"site_id": "SITE-SW-01", "region": "Southwest", "eligible_count": 251,
         "demographics": {"pct_female": 47, "pct_hispanic": 38, "pct_black": 7}},
        {"site_id": "SITE-NW-01", "region": "Northwest", "eligible_count": 176,
         "demographics": {"pct_female": 53, "pct_hispanic": 12, "pct_black": 5}},
    ],
    "phi_note": "All counts are aggregate and de-identified per 45 CFR 164.514.",
}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: SitePatientMatchingState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("rank_sites", "finalize"),
    }


def _claims(state: SitePatientMatchingState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-epidemiologist", "custom:hcls_role": "EPIDEMIOLOGIST",
    }


def intake(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "ANALYZING"
    state["audit_trail"].append(_audit(
        state, "Intake of site matching request for " + str(state.get("study_id")), "intake"
    ))
    state["completed_steps"].append("intake")
    return state


def translate_criteria(state: SitePatientMatchingState) -> SitePatientMatchingState:
    """Translate natural-language eligibility criteria using eligibility_translator."""
    state["current_step"] = "translate_criteria"
    criteria = state.get("eligibility_criteria", {})
    indication = state.get("indication", "")

    query = eligibility_translator.translate(criteria, indication)
    state["cohort_query"] = query

    state["audit_trail"].append(_audit(
        state,
        f"Translated eligibility criteria: {query.get('translated_fields', 0)} fields,"
        f" {len(query.get('filters', []))} inclusion filters,"
        f" {len(query.get('exclusion_filters', []))} exclusion filters",
        "translate_criteria",
    ))
    state["completed_steps"].append("translate_criteria")
    return state


def run_cohort_query(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "run_cohort_query"
    claims = _claims(state)
    sources = []

    try:
        gateway_tools.run_cohort_query(claims, state.get("cohort_query", {}))
        sources.append("rwd")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "run_cohort_query", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })

    existing = state.get("cohort_results", {})
    if isinstance(existing, dict) and existing.get("site_counts"):
        sources.append("rwd(pre-seeded)")
    else:
        state["cohort_results"] = _DEMO_COHORT_RESULTS

    try:
        status = gateway_tools.get_study_status(claims, state.get("study_id", ""))
        state["site_statuses"] = [status] if (isinstance(status, dict) and status) else []
        sources.append("ctms")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "run_cohort_query", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })
        state.setdefault("site_statuses", [])

    state["audit_trail"].append(_audit(
        state, "Ran de-identified cohort query (aggregate only)", "run_cohort_query", sources,
    ))
    state["completed_steps"].append("run_cohort_query")
    return state


def estimate_cohorts(state: SitePatientMatchingState) -> SitePatientMatchingState:
    """Use cohort_estimator to project enrollment feasibility per site and portfolio."""
    state["current_step"] = "estimate_cohorts"
    cohort = state.get("cohort_results", {})
    site_counts = cohort.get("site_counts", [])
    target = int(state.get("target_enrollment", 1))

    portfolio = cohort_estimator.estimate_portfolio(
        site_counts=site_counts if isinstance(site_counts, list) else [],
        target_enrollment=target,
    )
    state["cohort_estimates"] = portfolio

    state["audit_trail"].append(_audit(
        state,
        f"Cohort estimate: {portfolio.get('total_projected_enrollees', 0)} projected enrollees"
        f" vs target {target}; portfolio feasible: {portfolio.get('portfolio_feasible')}",
        "estimate_cohorts",
    ))
    state["completed_steps"].append("estimate_cohorts")
    return state


def rank_sites(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "rank_sites"
    cohort = state.get("cohort_results", {})
    site_counts = cohort.get("site_counts", [])

    if not isinstance(site_counts, list):
        site_counts = _DEMO_COHORT_RESULTS["site_counts"]

    ranked = sorted(
        site_counts,
        key=lambda s: s.get("eligible_count", 0) if isinstance(s, dict) else 0,
        reverse=True,
    )
    for i, site in enumerate(ranked):
        if isinstance(site, dict):
            site["rank"] = i + 1

    state["site_rankings"] = ranked

    flags: List[Dict[str, Any]] = []
    for site in ranked[:5]:
        if not isinstance(site, dict):
            continue
        demo = site.get("demographics", {})
        if isinstance(demo, dict) and demo.get("pct_black", 0) < 13:
            flags.append({
                "site_id": site["site_id"],
                "demographic": "Black/African American",
                "site_pct": demo.get("pct_black", 0),
                "benchmark_pct": 13,
                "description": (
                    "Site " + site["site_id"] + ": Black/African American representation "
                    "(" + str(demo.get("pct_black", 0)) + "%) below US prevalence benchmark (13%). "
                    "Recommend targeted outreach."
                ),
                "severity": "MODERATE",
            })

    state["fairness_flags"] = flags
    state["audit_trail"].append(_audit(
        state, f"Ranked {len(ranked)} sites; {len(flags)} fairness flag(s)", "rank_sites",
    ))
    state["completed_steps"].append("rank_sites")
    return state


def fairness_review(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "fairness_review"
    out = site_ranker.draft_report(dict(state))
    state["ranking_report"] = out["ranking_report"]
    state["drafted_by"] = out["drafted_by"]

    text = state.get("ranking_report", "")
    state["quality_findings"] = fairness_checker.quality_findings(text)
    state["grounding_report"] = fairness_checker.grounding_findings(text, dict(state))

    grounding = state.get("grounding_report", {})
    findings = state.get("quality_findings", [])
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])

    critical_equity = any(
        f.get("severity") == "CRITICAL" for f in state.get("fairness_flags", [])
    )
    if critical_equity:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_RANKING

    state["audit_trail"].append(_audit(
        state, "Drafted ranking report + fairness/grounding checks",
        "fairness_review", model=out["drafted_by"],
    ))
    state["completed_steps"].append("fairness_review")
    return state


def routing_decision(state: SitePatientMatchingState) -> str:
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "rank_sites"
    return "human_review_gate"


def human_review_gate(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state, "Awaiting human review of site ranking and fairness flags",
                 "human_review_gate"),
        "actor": "system", "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: SitePatientMatchingState) -> SitePatientMatchingState:
    state["current_step"] = "finalize"
    state["case_status"] = "FINALIZED"
    state["audit_trail"].append(_audit(
        state, "Site ranking finalized (post human approval)", "finalize", ["rwd", "ctms"],
    ))
    state["completed_steps"].append("finalize")
    return state
