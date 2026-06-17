# agent/state.py
# ============================================================
# ProtocolDesignState — state for clinical protocol design workflow.
#
# Context: The agent supports early protocol authoring — searching regulatory
# guidance and precedent, estimating feasibility via RWD, assessing operational
# and regulatory risks, and drafting protocol sections (endpoints, eligibility,
# schedule). It does NOT finalize or approve protocols without a qualified
# medical/clinical reviewer. ICH E6(R2) / GCP compliant.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for a drafted protocol section."""
    APPROVE_DRAFT = "APPROVE_DRAFT"      # clean: route to human reviewer
    REVISE = "REVISE"                    # grounding/regulatory issues
    ESCALATE = "ESCALATE"               # material regulatory risk


class ProtocolDesignState(TypedDict, total=False):
    # ── Request / context ─────────────────────────────────────────────────────
    request_id: str
    indication: str
    phase: str               # Phase 1 | Phase 2 | Phase 3 | Phase 2/3
    therapeutic_area: str
    primary_objective: str
    target_population: str
    study_design: str        # RCT | Single-arm | Cross-over | Adaptive
    instructions: str

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── Regulatory intelligence ───────────────────────────────────────────────
    guidance_hits: List[Dict[str, Any]]   # rim.search_guidance results

    # ── Feasibility data ──────────────────────────────────────────────────────
    cohort_estimate: Dict[str, Any]          # rwd.run_cohort_query (aggregate)
    study_status_refs: List[Dict[str, Any]]  # ctms.get_study_status (precedent)
    feasibility_assessment: Dict[str, Any]   # computed feasibility analysis

    # ── Draft protocol sections ───────────────────────────────────────────────
    draft_endpoints: Optional[str]
    draft_eligibility: Optional[str]
    draft_schedule: Optional[str]
    draft_protocol: str       # combined draft
    drafted_by: str

    # ── Risk assessment ───────────────────────────────────────────────────────
    operational_risks: List[str]
    regulatory_risks: List[str]

    # ── Quality checks ────────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    case_status: str
    revision_count: int

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    audit_trail: List[Dict[str, Any]]   # one entry per node; immutable after append
    protocol_id: str                     # assigned after finalization
    protocol_status: str                 # DRAFT | PENDING_REVIEW | SUBMITTED
    approval: Dict[str, Any]            # reviewer approval record
