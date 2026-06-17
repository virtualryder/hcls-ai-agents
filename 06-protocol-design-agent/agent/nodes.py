# agent/nodes.py
# ============================================================
# Node functions for the Protocol Design workflow.
#
# Workflow: intake -> search_guidance -> feasibility_estimate ->
#           draft_protocol_sections -> risk_assessment ->
#           quality_check -> [routing] ->
#           human_review_gate -> finalize -> END
#
# HITL is framework-enforced via interrupt_before=["human_review_gate"].
# A qualified medical or clinical reviewer must sign off before protocol
# sections are finalized or submitted to a health authority.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, ProtocolDesignState
from tools import (
    gateway_tools,
    guidance_searcher,
    feasibility_estimator,
    risk_assessor,
    protocol_drafter,
    protocol_checker,
)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: ProtocolDesignState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("draft_protocol_sections", "finalize"),
    }


def _claims(state: ProtocolDesignState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-clinical-scientist", "custom:hcls_role": "CLINICAL_SCIENTIST",
    }


def intake(state: ProtocolDesignState) -> ProtocolDesignState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "ANALYZING"
    state["audit_trail"].append(_audit(
        state,
        f"Intake of protocol design request: {state.get('indication')} ({state.get('phase')})",
        "intake",
    ))
    state["completed_steps"].append("intake")
    return state


def search_guidance(state: ProtocolDesignState) -> ProtocolDesignState:
    """Search RIM for regulatory guidance relevant to this trial design."""
    state["current_step"] = "search_guidance"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    claims = _claims(state)
    query = (
        f"{state.get('phase', '')} {state.get('indication', '')} "
        f"{state.get('therapeutic_area', '')} protocol guidance endpoint"
    )
    sources: List[str] = []

    try:
        hits = gateway_tools.search_guidance(claims, query)
        if hits:
            state["guidance_hits"] = hits
            sources.append("rim")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "search_guidance", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })

    # Demo fallback using guidance_searcher tool
    if not state.get("guidance_hits"):
        state["guidance_hits"] = guidance_searcher.search_guidance_demo(query, top_k=4)

    n_hits = len(state["guidance_hits"])
    state["audit_trail"].append(
        _audit(state,
               f"Searched regulatory guidance: {n_hits} document(s) found",
               "search_guidance", sources)
    )
    state["completed_steps"].append("search_guidance")
    return state


def feasibility_estimate(state: ProtocolDesignState) -> ProtocolDesignState:
    """Estimate enrollment feasibility from RWD cohort query and CTMS precedents."""
    state["current_step"] = "feasibility_estimate"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    claims = _claims(state)
    sources: List[str] = []

    cohort_query: Dict[str, Any] = {
        "indication": state.get("indication", ""),
        "phase": state.get("phase", ""),
        "target_population": state.get("target_population", ""),
    }

    # Try live gateway first
    try:
        result = gateway_tools.run_cohort_query(claims, cohort_query)
        if result:
            state["cohort_estimate"] = result
            sources.append("rwd")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "feasibility_estimate", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })

    # Demo fallback using feasibility_estimator tool
    if not state.get("cohort_estimate"):
        state["cohort_estimate"] = feasibility_estimator.estimate_cohort_demo(cohort_query)

    # Try CTMS for study precedents
    study_refs: List[Dict[str, Any]] = []
    try:
        study_id = f"PREC-{state.get('indication', '')[:10].upper().replace(' ', '-')}"
        ref = gateway_tools.get_study_status(claims, study_id)
        if ref:
            study_refs = [ref]
            if "ctms" not in sources:
                sources.append("ctms")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "feasibility_estimate_ctms", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })

    if not study_refs:
        study_refs = feasibility_estimator.get_study_precedents_demo(
            state.get("indication", ""), state.get("phase", "")
        )

    state["study_status_refs"] = study_refs

    # Compute feasibility assessment
    feasibility = feasibility_estimator.assess_feasibility(
        state["cohort_estimate"],
        enrollment_target=200,
    )
    state["feasibility_assessment"] = feasibility

    state["audit_trail"].append(
        _audit(state,
               f"Feasibility estimate: {state['cohort_estimate'].get('total_eligible', 'N/A')} "
               f"eligible patients; {len(study_refs)} study precedent(s)",
               "feasibility_estimate", sources)
    )
    state["completed_steps"].append("feasibility_estimate")
    return state


def draft_protocol_sections(state: ProtocolDesignState) -> ProtocolDesignState:
    """Draft protocol sections (endpoints, eligibility, schedule) using the LLM drafter."""
    state["current_step"] = "draft_protocol_sections"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    out = protocol_drafter.draft_protocol(dict(state))
    state["draft_protocol"] = out["draft_protocol"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(
        _audit(state,
               "Drafted protocol sections (endpoints, eligibility, schedule) — human review required",
               "draft_protocol_sections", model=out["drafted_by"])
    )
    state["completed_steps"].append("draft_protocol_sections")
    return state


def risk_assessment(state: ProtocolDesignState) -> ProtocolDesignState:
    """Assess operational and regulatory risks for this protocol design."""
    state["current_step"] = "risk_assessment"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])

    operational_risks = risk_assessor.assess_operational_risks(dict(state))
    regulatory_risks = risk_assessor.assess_regulatory_risks(dict(state))
    risk_summary = risk_assessor.summarize_risk_profile(operational_risks, regulatory_risks)

    state["operational_risks"] = operational_risks
    state["regulatory_risks"] = regulatory_risks

    state["audit_trail"].append(
        _audit(state,
               f"Risk assessment: {len(operational_risks)} operational, "
               f"{len(regulatory_risks)} regulatory risk(s). {risk_summary}",
               "risk_assessment")
    )
    state["completed_steps"].append("risk_assessment")
    return state


def quality_check(state: ProtocolDesignState) -> ProtocolDesignState:
    """Check protocol draft for completeness, speculative language, and grounding."""
    state["current_step"] = "quality_check"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    text = state.get("draft_protocol", "")
    state["quality_findings"] = protocol_checker.quality_findings(text)
    state["grounding_report"] = protocol_checker.grounding_findings(text, dict(state))

    grounding = state.get("grounding_report", {})
    findings = state.get("quality_findings", [])
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])

    # Disposition set INSIDE this node (not routing fn) — LangGraph persists node state mutations only
    reg_risks = state.get("regulatory_risks", [])
    critical = bool(reg_risks) and len(findings) > 0

    if critical:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_DRAFT

    state["audit_trail"].append(
        _audit(state,
               f"Quality check: {len(findings)} finding(s); grounded={grounding.get('grounded', True)}; action={state['recommended_action'].value}",
               "quality_check")
    )
    state["completed_steps"].append("quality_check")
    return state


def routing_decision(state: ProtocolDesignState) -> str:
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "draft_protocol_sections"
    return "human_review_gate"


def human_review_gate(state: ProtocolDesignState) -> ProtocolDesignState:
    state["current_step"] = "human_review_gate"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    state["protocol_status"] = "PENDING_REVIEW"
    entry = _audit(state, "Awaiting Medical Reviewer approval of protocol draft", "human_review_gate")
    entry["actor"] = "system"
    entry["human_review_required"] = True
    state["audit_trail"].append(entry)
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: ProtocolDesignState) -> ProtocolDesignState:
    state["current_step"] = "finalize"
    state.setdefault("audit_trail", [])
    state.setdefault("completed_steps", [])
    state.setdefault("errors", [])
    claims = _claims(state)
    approval = state.get("approval")
    try:
        res = gateway_tools.get_study_status(claims, {
            "request_id": state.get("request_id"),
            "indication": state.get("indication"),
            "phase": state.get("phase"),
            "protocol_summary": state.get("draft_protocol", "")[:300],
        })
        if getattr(res, "allowed", False):
            state["protocol_id"] = res.result.get("protocol_id", "PROTO-PENDING")
            state["protocol_status"] = "SUBMITTED"
        else:
            state["protocol_status"] = "PENDING_REVIEW"
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "finalize", "error": str(exc), "timestamp": _now(), "recoverable": True
        })
        state["protocol_status"] = "DRAFT"
    entry = _audit(state, "Finalized: protocol submitted for IND/CTA packaging (post reviewer approval)", "finalize", ["ctms"])
    entry["human_review_required"] = True
    entry["actor"] = state.get("acting_user_claims", {}).get("sub", "system")
    state["audit_trail"].append(entry)
    state["completed_steps"].append("finalize")
    return state
