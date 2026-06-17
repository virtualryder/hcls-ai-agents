# agent/nodes.py
# ============================================================
# Node functions for the Regulatory Writing workflow.
#
# Each node reads what it needs from RegulatoryWritingState, performs one step,
# writes its findings back, and appends an audit-trail entry (21 CFR Part 11).
# The AI assembles and drafts; a Regulatory Approver decides. The human_review
# gate is framework-enforced via interrupt_before in graph.py.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, RegulatoryWritingState
from tools import consistency_checker, gateway_tools, regulatory_intelligence, submission_drafter


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: RegulatoryWritingState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("draft_section", "finalize"),
    }


def _claims(state: RegulatoryWritingState) -> Dict[str, Any]:
    # Demo default: a Regulatory Author identity if none supplied.
    return state.get("acting_user_claims") or {
        "sub": "demo-author", "custom:hcls_role": "REGULATORY_AUTHOR",
    }


def intake(state: RegulatoryWritingState) -> RegulatoryWritingState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "DRAFTING"
    state["audit_trail"].append(_audit(state, f"Intake of {state.get('document_type')} request", "intake"))
    state["completed_steps"].append("intake")
    return state


def regulatory_intelligence_node(state: RegulatoryWritingState) -> RegulatoryWritingState:
    state["current_step"] = "regulatory_intelligence"
    claims = _claims(state)
    product = state.get("product", "DEMO-DRUG")
    query = f"{state.get('document_type','')} {state.get('target_authority','')} {state.get('indication','')}"
    try:
        state["obligations"] = gateway_tools.get_obligations(claims, product)
        state["guidance_hits"] = gateway_tools.search_guidance(claims, query)
        sources = ["rim"]
    except Exception as exc:  # gateway/platform absent -> note, continue (demo)
        state.setdefault("errors", []).append({"step": "regulatory_intelligence", "error": str(exc),
                                               "timestamp": _now(), "recoverable": True})
        state.setdefault("guidance_hits", [])
        sources = []
    state["audit_trail"].append(_audit(state, "Retrieved obligations and guidance",
                                       "regulatory_intelligence", sources))
    state["completed_steps"].append("regulatory_intelligence")
    return state


def evidence_assembly(state: RegulatoryWritingState) -> RegulatoryWritingState:
    state["current_step"] = "evidence_assembly"
    claims = _claims(state)
    docs = []
    for doc_id in state.get("source_doc_ids", []) or []:
        try:
            docs.append(gateway_tools.get_document(claims, doc_id))
        except Exception:
            pass
    if docs:
        state["source_documents"] = docs
    state.setdefault("source_documents", state.get("source_documents", []))
    state["audit_trail"].append(_audit(state, "Assembled source evidence corpus",
                                       "evidence_assembly", ["dms"]))
    state["completed_steps"].append("evidence_assembly")
    return state


def draft_section(state: RegulatoryWritingState) -> RegulatoryWritingState:
    state["current_step"] = "draft_section"
    out = submission_drafter.draft_section(dict(state))
    state["draft_text"] = out["draft_text"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(_audit(state, "Drafted regulated section",
                                       "draft_section", model=out["drafted_by"]))
    state["completed_steps"].append("draft_section")
    return state


def consistency_check(state: RegulatoryWritingState) -> RegulatoryWritingState:
    state["current_step"] = "consistency_check"
    text = state.get("draft_text", "")
    state["compliance_findings"] = consistency_checker.compliance_findings(text)
    state["grounding_report"] = consistency_checker.grounding_findings(text, dict(state))
    # Cross-reference check: guidance referenced should exist (illustrative).
    state["consistency_findings"] = (
        [] if state.get("guidance_hits") else ["no guidance referenced in regulatory intelligence step"]
    )

    # Disposition is set HERE (in a node) so it persists in state. The routing
    # function below is a pure read of recommended_action — LangGraph does not
    # persist mutations made inside a conditional-edge path function.
    grounding = state.get("grounding_report", {})
    compliance = state.get("compliance_findings", [])
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])
    severe = any("prohibited" in f for f in compliance)
    if severe:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or compliance) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_DRAFT

    state["audit_trail"].append(_audit(state, "Ran compliance + grounding checks", "consistency_check"))
    state["completed_steps"].append("consistency_check")
    return state


def routing_decision(state: RegulatoryWritingState) -> str:
    """Pure read of the disposition set in consistency_check (no state mutation)."""
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "draft_section"
    return "human_review_gate"


def human_review_gate(state: RegulatoryWritingState) -> RegulatoryWritingState:
    """HITL pause point. graph compiles with interrupt_before=[human_review_gate]."""
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state, "Awaiting Regulatory Approver review/sign-off", "human_review_gate"),
        "actor": "system", "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: RegulatoryWritingState) -> RegulatoryWritingState:
    """
    Create the submission draft in RIM (high-risk write) ONLY with a verified
    human approval bound at the gateway. Without approval the gateway returns
    PENDING_APPROVAL and no draft is created.
    """
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")  # set by the UI after human sign-off
    try:
        res = gateway_tools.create_submission_draft(
            claims,
            {"document_type": state.get("document_type"), "product": state.get("product"),
             "section_ref": state.get("section_ref"), "text_len": len(state.get("draft_text", ""))},
            approval=approval,
        )
        if getattr(res, "allowed", False):
            state["submission_draft_id"] = res.result.get("draft_id", "SUBM-DRAFT-PENDING")
            state["case_status"] = "SUBMITTED_DRAFT"
        else:
            state["case_status"] = "PENDING_REVIEW"
    except Exception as exc:
        state.setdefault("errors", []).append({"step": "finalize", "error": str(exc),
                                               "timestamp": _now(), "recoverable": True})
        state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append(_audit(state, "Finalized submission draft (post human approval)",
                                       "finalize", ["rim"]))
    state["completed_steps"].append("finalize")
    return state
