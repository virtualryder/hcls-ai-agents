# agent/state.py
# ============================================================
# QualityCAPAState — state for complaint/deviation CAPA workflow.
#
# Context: GMP/GCP regulated environment (21 CFR Part 820, ICH Q10).
# Agent classifies complaints, clusters similar events, proposes root-cause
# hypotheses, and drafts a CAPA plan. A Qualified Person must review and
# approve before any CAPA is created or closed in the QMS.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for a CAPA plan."""
    APPROVE_CAPA = "APPROVE_CAPA"        # clean: route to Qualified Person for sign-off
    REVISE = "REVISE"                    # grounding/completeness issues
    ESCALATE = "ESCALATE"               # critical safety/regulatory concern


class QualityCAPAState(TypedDict, total=False):
    # ── Request / context ─────────────────────────────────────────────────────
    request_id: str
    complaint_id: str
    event_type: str          # COMPLAINT | DEVIATION | OOS | AUDIT_FINDING
    product: str
    lot_number: str
    site: str
    description: str         # raw complaint/deviation description
    severity: str            # CRITICAL | MAJOR | MINOR

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── QMS data ──────────────────────────────────────────────────────────────
    complaint_record: Dict[str, Any]      # qms.get_complaint result
    similar_events: List[Dict[str, Any]]  # qms.search_similar results

    # ── Analysis outputs ──────────────────────────────────────────────────────
    classification: Dict[str, Any]        # event classification + risk
    clusters: List[Dict[str, Any]]        # similar event clusters
    root_cause_hypotheses: List[str]      # drafted root causes

    # ── Draft CAPA + checks ───────────────────────────────────────────────────
    capa_plan: str
    drafted_by: str
    grounding_report: Dict[str, Any]
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    capa_draft_id: str        # created CAPA draft ID (post QP approval)
    case_status: str          # CLASSIFYING | PENDING_REVIEW | APPROVED | CAPA_CREATED
    revision_count: int

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # ── Audit trail (21 CFR Part 820) ─────────────────────────────────────────
    audit_trail: List[Dict[str, Any]]
