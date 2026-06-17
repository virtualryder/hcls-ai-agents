# agent/state.py
# ============================================================
# RWEHEORState — state object for the RWE/HEOR analysis workflow.
#
# Context of use (HEOR, epidemiology, 21 CFR Part 11 audit):
# The LLM orchestrates cohort design and evidence synthesis;
# validated statistical computation runs separately (cohort_query_runner.py).
# All numbers must be traceable to the RWD cohort output.
# An Epidemiologist reviews all findings before they are used in
# publications or regulatory submissions.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for an RWE/HEOR evidence synthesis."""
    APPROVE_SYNTHESIS = "APPROVE_SYNTHESIS"  # grounded, clean: route to Epidemiologist
    REVISE = "REVISE"                        # grounding/traceability issues: re-draft
    ESCALATE = "ESCALATE"                    # material data quality / causal language concern


class RWEHEORState(TypedDict, total=False):
    # ── Research question / request ──────────────────────────────────────────
    request_id: str
    research_question: str
    study_design_type: str    # Retrospective Cohort | Comparative Cohort | Cross-sectional Cohort
    indication: str
    intervention: str
    comparator: str
    outcome: str
    time_horizon: str         # e.g., "12 months", "24 months"
    data_source: str          # e.g., "US Commercial Claims (Optum CDM)"
    instructions: str

    # ── Acting user (gateway adoption) ───────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── Cohort definition ────────────────────────────────────────────────────
    cohort_definition: Dict[str, Any]       # computable spec from cohort_definer
    cohort_definition_valid: bool
    cohort_definition_issues: List[str]

    # ── RWD query results (de-identified aggregate only) ─────────────────────
    cohort_results: Dict[str, Any]          # rwd.run_cohort_query output
    summary_statistics: Dict[str, Any]      # validated compute from cohort_query_runner

    # ── Data quality ─────────────────────────────────────────────────────────
    data_quality: Dict[str, Any]            # from data_quality_assessor.assess_data_quality

    # ── Evidence synthesis (LLM-drafted) ─────────────────────────────────────
    evidence_synthesis: str                 # narrative synthesis
    drafted_by: str                         # demo-stub | bedrock | anthropic

    # ── Grounding + quality gates ─────────────────────────────────────────────
    grounding_report: Dict[str, Any]        # verify_grounding result
    quality_findings: List[str]             # causal language, missing elements

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    case_status: str          # ANALYZING | PENDING_REVIEW | APPROVED | FINALIZED
    revision_count: int

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # ── Audit trail ───────────────────────────────────────────────────────────
    # Each entry: timestamp, actor, action, node, data_sources_accessed,
    # ai_model_used, human_review_required.
    audit_trail: List[Dict[str, Any]]
