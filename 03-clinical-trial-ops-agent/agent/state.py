# agent/state.py -- ClinicalTrialOpsState
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

class RecommendedAction(str, Enum):
    APPROVE_BRIEF = "APPROVE_BRIEF"
    REVISE = "REVISE"
    ESCALATE = "ESCALATE"

class ClinicalTrialOpsState(TypedDict, total=False):
    request_id: str
    study_id: str
    protocol_id: str
    sponsor: str
    indication: str
    review_period: str
    instructions: str
    acting_user_claims: Dict[str, Any]
    study_status: Dict[str, Any]
    tmf_data: Dict[str, Any]
    tmf_completeness: Dict[str, Any]
    subject_data: List[Dict[str, Any]]
    tmf_analysis: Dict[str, Any]
    enrollment_metrics: Dict[str, Any]
    risk_score: Dict[str, Any]
    detected_issues: List[Dict[str, Any]]
    missing_data_flags: List[Dict[str, Any]]
    deviation_flags: List[Dict[str, Any]]
    data_queries: List[Dict[str, Any]]
    query_summary: Dict[str, Any]
    brief_text: str
    draft_text: str
    drafted_by: str
    grounding_report: Dict[str, Any]
    quality_findings: List[str]
    recommended_action: RecommendedAction
    edc_query_ids: List[str]
    case_status: str
    revision_count: int
    approval: Optional[Dict[str, Any]]
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
