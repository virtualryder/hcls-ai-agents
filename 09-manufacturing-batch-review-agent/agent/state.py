# agent/state.py
# ============================================================
# BatchReviewState — state object for a Manufacturing Batch-Review workflow.
#
# Context of use (cGMP 21 CFR Part 211, 21 CFR Part 11): the agent READS an
# electronic batch record (EBR/MES) + QC results (LIMS), SCANS for deviations,
# out-of-specification (OOS) results, missing steps, and incomplete e-signatures
# ("review by exception"), and DRAFTS a disposition (exception report +
# recommended release/hold) for a QA Reviewer. It does NOT release or reject a
# batch: a Qualified Person / QA Reviewer signs the disposition at the gateway.
# Every field maps to a batch-record review requirement or an audit element.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    """Disposition recommendation for a reviewed batch (QA decides, not the agent)."""
    RECOMMEND_RELEASE = "RECOMMEND_RELEASE"   # no open exceptions -> QA release sign-off
    RECOMMEND_HOLD = "RECOMMEND_HOLD"         # open exception(s) -> QA review/hold
    REVISE = "REVISE"                         # draft quality issue -> redraft (bounded)
    ESCALATE = "ESCALATE"                     # critical exception / data-integrity -> senior QA


class Severity(str, Enum):
    CRITICAL = "CRITICAL"   # OOS, missing critical step, unsigned critical record
    MAJOR = "MAJOR"         # out-of-trend / in-process deviation requiring investigation
    MINOR = "MINOR"         # documentation discrepancy, non-critical


class BatchReviewState(TypedDict, total=False):
    # ── Intake / source ───────────────────────────────────────────────────────
    review_id: str
    batch_id: str
    product: str
    raw_batch_record: Dict[str, Any]    # the EBR payload (steps, params, e-signatures)
    lims_results: List[Dict[str, Any]]  # QC test results pulled from LIMS

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── Exception scan (review by exception) ──────────────────────────────────
    exceptions: List[Dict[str, Any]]     # each: {code, severity, step, detail, source}
    exception_count: int
    critical_count: int
    has_open_exceptions: bool
    right_first_time: bool               # True if zero exceptions

    # ── Disposition draft ─────────────────────────────────────────────────────
    exception_report: str
    disposition_recommendation: str      # RELEASE | HOLD (recommendation only)
    report_drafted_by: str               # bedrock | anthropic | demo-stub

    # ── Quality check ─────────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    required_elements_present: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition outcome ───────────────────────────────────────────────────
    disposition_id: Optional[str]
    batch_status: str            # INTAKE | UNDER_REVIEW | PENDING_QA | RELEASED | HELD | PENDING
    revision_count: int

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]
    approval: Optional[Dict[str, Any]]   # verified QA approval bound at the gateway

    # ── Audit trail (21 CFR Part 11 / Part 211.192) ───────────────────────────
    audit_trail: List[Dict[str, Any]]
