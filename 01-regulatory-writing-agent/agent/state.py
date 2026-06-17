# agent/state.py
# ============================================================
# RegulatoryWritingState — state object for a regulatory authoring task.
#
# Context of use (FDA/EMA good-AI principles, Jan 2026): the agent ASSEMBLES
# evidence and DRAFTS regulated submission content (benefit-risk summaries, CSR
# sections, responses to health-authority questions). It does NOT decide medical
# or regulatory strategy and NEVER finalizes/submits without a qualified
# Regulatory Approver. Every field maps to an authoring, traceability, or audit
# requirement examiners expect (ICH M4/CTD structure; 21 CFR Part 11 audit trail).
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for a drafted regulatory artifact."""
    APPROVE_DRAFT = "APPROVE_DRAFT"   # clean: route to human approver for sign-off
    REVISE = "REVISE"                 # grounding/consistency issues: send back to draft
    ESCALATE = "ESCALATE"             # material compliance concern: senior regulatory review


class RegulatoryWritingState(TypedDict, total=False):
    # ── Request / context ─────────────────────────────────────────────────────
    request_id: str
    document_type: str          # BENEFIT_RISK_SUMMARY | CSR_SECTION | HA_QUESTION_RESPONSE | LABELING_SECTION
    product: str
    indication: str
    target_authority: str       # FDA | EMA | PMDA | MHRA | ...
    section_ref: str            # e.g., "CTD Module 2.5", "Response to Question 14"
    instructions: str           # author's instructions / scope

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    # Verified IdP claims for the human on whose behalf this runs. Gateway-backed
    # tools require these; absent them the MCP gateway denies (fail-closed).
    acting_user_claims: Dict[str, Any]

    # ── Regulatory intelligence ───────────────────────────────────────────────
    obligations: List[Dict[str, Any]]      # rim.get_obligations
    guidance_hits: List[Dict[str, Any]]    # rim.search_guidance

    # ── Source evidence (the grounding corpus) ────────────────────────────────
    source_documents: List[Dict[str, Any]] # dms.get_document results
    study_data: Dict[str, Any]             # structured facts: endpoints, N, results

    # ── Draft + checks ────────────────────────────────────────────────────────
    draft_text: str
    drafted_by: str                        # bedrock | anthropic | demo-stub
    grounding_report: Dict[str, Any]       # governance.grounding output
    compliance_findings: List[str]         # off-label/promotional/missing-element flags
    consistency_findings: List[str]        # cross-reference / figure-claim mismatches

    recommended_action: RecommendedAction

    # ── Disposition / submission ──────────────────────────────────────────────
    submission_draft_id: str
    case_status: str            # DRAFTING | PENDING_REVIEW | APPROVED | SUBMITTED_DRAFT
    revision_count: int

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # ── Audit trail (21 CFR Part 11) ──────────────────────────────────────────
    # Each entry: timestamp, actor, action, node, data_sources_accessed,
    # ai_model_used, human_review_required.
    audit_trail: List[Dict[str, Any]]
