# agent/state.py
# ============================================================
# MedicalAffairsMSLState — state for MSL pre-call brief workflow.
#
# Context of use: Medical Science Liaisons operate under strict compliance
# rules — all content must be on-label, cited from approved materials, and
# reviewed by a Medical Affairs Approver before use. The agent drafts
# pre-call briefs from HCP profiles and approved content; it never generates
# off-label claims and never finalizes content without human sign-off.
# Off-label or promotional findings always escalate (never just revise).
# After Approver sign-off, the brief is submitted to MLR review (HIGH-RISK).
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for an MSL pre-call brief."""
    APPROVE_BRIEF = "APPROVE_BRIEF"        # compliant, grounded: route to Approver
    REVISE = "REVISE"                      # grounding issues (no compliance flag)
    ESCALATE = "ESCALATE"                  # off-label or promotional finding


class MedicalAffairsMSLState(TypedDict, total=False):
    # ── Request / context ─────────────────────────────────────────────────────
    request_id: str
    hcp_id: str
    hcp_name: str
    topic: str              # clinical topic / product area
    meeting_date: str
    meeting_purpose: str    # e.g., "Respond to unsolicited request"
    instructions: str

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── HCP profile (from CRM) ────────────────────────────────────────────────
    hcp_profile: Dict[str, Any]           # crm.get_hcp result + enriched fields
    hcp_profile_valid: bool
    hcp_profile_issues: List[str]

    # ── Approved documents (from DMS) ─────────────────────────────────────────
    approved_documents: List[Dict[str, Any]]  # dms.get_document results
    approved_doc_ids: List[str]
    document_validation: Dict[str, Any]       # from content_retriever.validate_documents
    citation_index: Dict[str, str]            # shorthand -> full title

    # ── Next best actions ─────────────────────────────────────────────────────
    next_best_actions: Dict[str, Any]         # from next_best_action.recommend_actions

    # ── Draft brief + compliance checks ──────────────────────────────────────
    brief_text: str
    drafted_by: str
    compliance_findings: List[str]        # off-label / promotional flags
    grounding_report: Dict[str, Any]      # numbers traceable to approved content

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    mlr_submission_id: Optional[str]    # MLR review ID (created post approval, high-risk)
    case_status: str                    # DRAFTING | PENDING_REVIEW | APPROVED | SUBMITTED_MLR
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
