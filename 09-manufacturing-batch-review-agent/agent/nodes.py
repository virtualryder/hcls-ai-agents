# agent/nodes.py
# ============================================================
# Node functions for the Manufacturing Batch-Review workflow.
#
# Each node reads what it needs from BatchReviewState, performs one step, writes
# its findings back, and appends an audit-trail entry (21 CFR Part 11 / Part
# 211.192). The AI loads, scans by exception, and drafts a disposition; a QA
# Reviewer decides release/reject. The human_review_gate is framework-enforced
# via interrupt_before in graph.py.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import BatchReviewState, RecommendedAction
from tools import gateway_tools, exception_scanner, disposition_drafter, quality_checker

_MAX_REVISIONS = 2


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: BatchReviewState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("disposition_draft", "finalize"),
    }


def _claims(state: BatchReviewState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-mfg-operator", "custom:hcls_role": "MFG_OPERATOR",
    }


def intake(state: BatchReviewState) -> BatchReviewState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state.setdefault("review_id", f"BR-{state.get('batch_id','UNKNOWN')}")
    state["batch_status"] = "INTAKE"
    state["audit_trail"].append(
        _audit(state, f"Intake of batch {state.get('batch_id','UNKNOWN')} for review", "intake")
    )
    state["completed_steps"].append("intake")
    return state


def load_batch(state: BatchReviewState) -> BatchReviewState:
    """Pull the electronic batch record (MES) + QC results (LIMS) via the gateway.

    Falls back to any inline record supplied on the state (demo / unit tests) so
    the pipeline runs without the gateway, but production reads flow through it.
    """
    state["current_step"] = "load_batch"
    claims = _claims(state)
    batch_id = state.get("batch_id", "")
    sources = []
    if not state.get("raw_batch_record"):
        try:
            rec = gateway_tools.get_batch_record(claims, batch_id)
            if rec:
                state["raw_batch_record"] = rec
                sources.append("mes")
        except Exception as exc:
            state.setdefault("errors", []).append(
                {"step": "load_batch_mes", "error": str(exc), "timestamp": _now(), "recoverable": True}
            )
    if not state.get("lims_results"):
        try:
            res = gateway_tools.get_lims_results(claims, batch_id)
            if res:
                state["lims_results"] = res
                sources.append("lims")
        except Exception as exc:
            state.setdefault("errors", []).append(
                {"step": "load_batch_lims", "error": str(exc), "timestamp": _now(), "recoverable": True}
            )
    state.setdefault("raw_batch_record", {})
    state.setdefault("lims_results", [])
    state["product"] = state.get("product") or state["raw_batch_record"].get("product", "UNKNOWN-PRODUCT")
    state["batch_status"] = "UNDER_REVIEW"
    state["audit_trail"].append(
        _audit(state, "Loaded electronic batch record + LIMS results", "load_batch", sources=sources)
    )
    state["completed_steps"].append("load_batch")
    return state


def exception_scan(state: BatchReviewState) -> BatchReviewState:
    """Review-by-exception: deterministic scan for OOS, out-of-limit, missing steps,
    and incomplete e-signatures. This is the core control — every flag traces to data."""
    state["current_step"] = "exception_scan"
    result = exception_scanner.scan(
        state.get("raw_batch_record", {}), state.get("lims_results", [])
    )
    state["exceptions"] = result["exceptions"]
    state["exception_count"] = result["exception_count"]
    state["critical_count"] = result["critical_count"]
    state["has_open_exceptions"] = result["exception_count"] > 0
    state["right_first_time"] = result["exception_count"] == 0
    state["audit_trail"].append(
        _audit(state,
               f"Scanned by exception: {result['exception_count']} exception(s), "
               f"{result['critical_count']} critical", "exception_scan")
    )
    state["completed_steps"].append("exception_scan")
    return state


def disposition_draft(state: BatchReviewState) -> BatchReviewState:
    """Draft the exception report + a release/hold recommendation (QA decides)."""
    state["current_step"] = "disposition_draft"
    drafted = disposition_drafter.draft(dict(state))
    state["exception_report"] = drafted["exception_report"]
    state["report_drafted_by"] = drafted["report_drafted_by"]
    state["disposition_recommendation"] = "HOLD" if state.get("has_open_exceptions") else "RELEASE"
    state["audit_trail"].append(
        _audit(state, "Drafted batch exception report + recommendation", "disposition_draft",
               model=drafted["report_drafted_by"])
    )
    state["completed_steps"].append("disposition_draft")
    return state


def quality_check(state: BatchReviewState) -> BatchReviewState:
    """Grounding + required-element gates before QA sees the report; sets the
    routing disposition. Mirrors the eval harness bar."""
    state["current_step"] = "quality_check"
    result = quality_checker.check(dict(state))
    state["grounding_report"] = result["grounding_report"]
    state["required_elements_present"] = result["required_elements_present"]
    state["quality_findings"] = result["quality_findings"]

    grounded = result["grounding_report"].get("grounded", True)
    draft_ok = grounded and result["required_elements_present"]
    revisions = state.get("revision_count", 0)

    if not draft_ok and revisions < _MAX_REVISIONS:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = revisions + 1
    elif state.get("critical_count", 0) > 0:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif state.get("has_open_exceptions"):
        state["recommended_action"] = RecommendedAction.RECOMMEND_HOLD
    else:
        state["recommended_action"] = RecommendedAction.RECOMMEND_RELEASE

    state["audit_trail"].append(
        _audit(state, "Ran grounding + required-element quality checks on the report", "quality_check")
    )
    state["completed_steps"].append("quality_check")
    return state


def routing_decision(state: BatchReviewState) -> str:
    """Pure read of the disposition set in quality_check (no state mutation)."""
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "disposition_draft"
    return "human_review_gate"


def human_review_gate(state: BatchReviewState) -> BatchReviewState:
    """HITL pause point. Graph compiles with interrupt_before=[human_review_gate]."""
    state["current_step"] = "human_review_gate"
    state["batch_status"] = "PENDING_QA"
    state["audit_trail"].append({
        **_audit(state, "Awaiting QA reviewer release/reject sign-off", "human_review_gate"),
        "actor": "system",
        "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: BatchReviewState) -> BatchReviewState:
    """Record the QA disposition (HIGH-RISK write) ONLY with a verified human
    approval bound at the gateway. Without approval the gateway returns PENDING
    and no disposition is recorded."""
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")
    try:
        res = gateway_tools.record_disposition(
            claims,
            {
                "batch_id": state.get("batch_id"),
                "recommendation": state.get("disposition_recommendation"),
                "exception_count": state.get("exception_count"),
                "critical_count": state.get("critical_count"),
            },
            approval=approval,
        )
        if getattr(res, "allowed", False):
            decision = (res.result or {}).get("decision") or state.get("disposition_recommendation")
            state["disposition_id"] = (res.result or {}).get("disposition_id", "DISP-PENDING")
            state["batch_status"] = "RELEASED" if decision == "RELEASE" else "HELD"
        else:
            state["batch_status"] = "PENDING"
    except Exception as exc:
        state.setdefault("errors", []).append(
            {"step": "finalize", "error": str(exc), "timestamp": _now(), "recoverable": True}
        )
        state["batch_status"] = "PENDING"

    state["audit_trail"].append({
        **_audit(state, "Finalized batch disposition — audit trail locked", "finalize"),
        "human_review_required": True,
        "actor": state.get("acting_user_claims", {}).get("sub", "system"),
    })
    state["completed_steps"].append("finalize")
    return state
