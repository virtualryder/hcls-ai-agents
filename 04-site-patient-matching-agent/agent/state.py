# agent/state.py
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, TypedDict


class RecommendedAction(str, Enum):
    APPROVE_RANKING = "APPROVE_RANKING"
    REVISE = "REVISE"
    ESCALATE = "ESCALATE"


class SitePatientMatchingState(TypedDict, total=False):
    # Request / context
    request_id: str
    study_id: str
    protocol_id: str
    indication: str
    eligibility_criteria: Dict[str, Any]
    target_enrollment: int
    instructions: str

    # Acting user (gateway adoption)
    acting_user_claims: Dict[str, Any]

    # Computed eligibility logic
    cohort_query: Dict[str, Any]

    # RWD + CTMS results
    cohort_results: Dict[str, Any]
    site_statuses: List[Dict[str, Any]]

    # Analysis outputs
    site_rankings: List[Dict[str, Any]]
    fairness_flags: List[Dict[str, Any]]
    cohort_estimates: Dict[str, Any]     # NEW: per-site and portfolio feasibility estimates

    # Draft output + checks
    ranking_report: str
    drafted_by: str
    grounding_report: Dict[str, Any]
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # Disposition
    case_status: str
    revision_count: int

    # LangGraph / UI infra
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # Audit trail
    audit_trail: List[Dict[str, Any]]
