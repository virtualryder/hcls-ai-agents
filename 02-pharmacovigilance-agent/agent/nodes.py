# agent/nodes.py
# ============================================================
# Node functions for the Pharmacovigilance ICSR Intake workflow.
#
# Each node reads what it needs from PharmacovigilanceState, performs one step,
# writes its findings back, and appends an audit-trail entry (21 CFR Part 11 /
# GVP Module VI). The AI parses, extracts, codes, and drafts; a PV Medical
# Reviewer decides seriousness, causality, and submission. The human_review_gate
# is framework-enforced via interrupt_before in graph.py.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, PharmacovigilanceState
from tools import (
    gateway_tools,
    case_extractor,
    coder,
    duplicate_checker,
    seriousness_assessor,
    narrative_drafter,
    quality_checker,
)

# Minimum match-score threshold for a gateway duplicate result to be flagged.
# The fixture returns a low-confidence result (0.34); only flag confirmed matches.
_DUPLICATE_MIN_SCORE = 0.5


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: PharmacovigilanceState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("narrative_draft", "finalize"),
    }


def _claims(state: PharmacovigilanceState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-pv-processor", "custom:hcls_role": "PV_PROCESSOR",
    }


def intake(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "INTAKE"
    state["audit_trail"].append(
        _audit(state, f"Intake of {state.get('source_type','UNKNOWN')} AE source record", "intake")
    )
    state["completed_steps"].append("intake")
    return state


def validity_check(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "validity_check"
    raw = state.get("raw_source", "")
    result = case_extractor.check_validity(raw)
    state["has_identifiable_patient"] = result["has_identifiable_patient"]
    state["has_identifiable_reporter"] = result["has_identifiable_reporter"]
    state["has_suspect_product"] = result["has_suspect_product"]
    state["has_adverse_event"] = result["has_adverse_event"]
    state["is_valid_icsr"] = result["is_valid_icsr"]
    state["validity_notes"] = result["validity_notes"]
    state["audit_trail"].append(
        _audit(state, "Checked ICSR validity (4 mandatory elements)", "validity_check")
    )
    state["completed_steps"].append("validity_check")
    return state


def extract_fields(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "extract_fields"
    raw = state.get("raw_source", "")
    fields = case_extractor.extract(raw)
    for k, v in fields.items():
        state[k] = v  # type: ignore[literal-required]
    state["audit_trail"].append(
        _audit(state, "Extracted E2B(R3) case fields from source record", "extract_fields")
    )
    state["completed_steps"].append("extract_fields")
    return state


def code_terms(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "code_terms"
    claims = _claims(state)
    event = state.get("event_description", "")
    drug = state.get("suspect_drug", "")
    try:
        meddra_result = gateway_tools.code_meddra_term(claims, event)
        state["meddra_pt"] = meddra_result.get("pt")
        state["meddra_pt_code"] = meddra_result.get("pt_code")
        state["meddra_soc"] = meddra_result.get("soc")
        sources = ["meddra"]
    except Exception as exc:
        state.setdefault("errors", []).append(
            {"step": "code_terms_meddra", "error": str(exc), "timestamp": _now(), "recoverable": True}
        )
        coded = coder.code_event_demo(event)
        state["meddra_pt"] = coded["pt"]
        state["meddra_pt_code"] = coded["pt_code"]
        state["meddra_soc"] = coded["soc"]
        sources = []
    try:
        whodrug_result = gateway_tools.code_whodrug(claims, drug)
        state["whodrug_name"] = whodrug_result.get("name")
        state["whodrug_atc"] = whodrug_result.get("atc")
        if "whodrug" not in sources:
            sources.append("whodrug")
    except Exception as exc:
        state.setdefault("errors", []).append(
            {"step": "code_terms_whodrug", "error": str(exc), "timestamp": _now(), "recoverable": True}
        )
        coded_drug = coder.code_drug_demo(drug)
        state["whodrug_name"] = coded_drug["name"]
        state["whodrug_atc"] = coded_drug["atc"]
    state["audit_trail"].append(
        _audit(state, "Coded adverse event (MedDRA PT) and suspect drug (WHODrug)", "code_terms", sources)
    )
    state["completed_steps"].append("code_terms")
    return state


def duplicate_search(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "duplicate_search"
    claims = _claims(state)
    try:
        candidates = gateway_tools.search_duplicates(
            claims,
            {
                "patient_age": state.get("patient_age"),
                "suspect_drug": state.get("suspect_drug"),
                "meddra_pt": state.get("meddra_pt"),
                "reporter_name": state.get("reporter_name"),
                "event_onset_date": state.get("event_onset_date"),
            },
        )
        sources = ["safety"]
    except Exception as exc:
        state.setdefault("errors", []).append(
            {"step": "duplicate_search", "error": str(exc), "timestamp": _now(), "recoverable": True}
        )
        candidates = duplicate_checker.demo_search(dict(state))
        sources = []

    # Filter to confirmed duplicates only (min match score threshold).
    # Low-confidence fixture/gateway results (e.g., 0.34) are not flagged.
    confirmed = [c for c in candidates if c.get("match_score", 0) >= _DUPLICATE_MIN_SCORE]
    state["duplicate_candidates"] = confirmed
    state["is_duplicate"] = len(confirmed) > 0

    state["audit_trail"].append(
        _audit(state, "Searched safety database for duplicate ICSRs", "duplicate_search", sources)
    )
    state["completed_steps"].append("duplicate_search")
    return state


def seriousness_assessment(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "seriousness_assessment"
    result = seriousness_assessor.assess(dict(state))
    state["is_serious"] = result["is_serious"]
    state["seriousness_criteria"] = result["seriousness_criteria"]
    state["expectedness"] = result.get("expectedness", "UNKNOWN")
    state["reporting_clock_days"] = result.get("reporting_clock_days")
    state["causality_assessment"] = result.get("causality_assessment", "UNKNOWN")
    state["audit_trail"].append(
        _audit(state, "Assessed seriousness, expectedness, and reporting clock", "seriousness_assessment")
    )
    state["completed_steps"].append("seriousness_assessment")
    return state


def narrative_draft(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "narrative_draft"
    out = narrative_drafter.draft_narrative(dict(state))
    state["narrative_text"] = out["narrative_text"]
    state["narrative_drafted_by"] = out["narrative_drafted_by"]
    state["audit_trail"].append(
        _audit(state, "Drafted ICSR narrative (CIOMS/E2B-style)",
               "narrative_draft", model=out["narrative_drafted_by"])
    )
    state["completed_steps"].append("narrative_draft")
    return state


def quality_check(state: PharmacovigilanceState) -> PharmacovigilanceState:
    state["current_step"] = "quality_check"
    result = quality_checker.check(dict(state))
    state["grounding_report"] = result["grounding_report"]
    state["phi_check_passed"] = result["phi_check_passed"]
    state["required_elements_present"] = result["required_elements_present"]
    state["quality_findings"] = result["quality_findings"]

    # Disposition is set HERE (in a node) so it persists in state. The routing
    # function below is a pure read of recommended_action — LangGraph does not
    # persist mutations made inside a conditional-edge path function.
    phi_leak = not result["phi_check_passed"]
    grounding = result["grounding_report"]
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])
    findings = result["quality_findings"]

    if phi_leak:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or not result["required_elements_present"]) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_DRAFT

    state["audit_trail"].append(
        _audit(state, "Ran grounding + PHI + required-element quality checks", "quality_check")
    )
    state["completed_steps"].append("quality_check")
    return state


def routing_decision(state: PharmacovigilanceState) -> str:
    """Pure read of the disposition set in quality_check (no state mutation)."""
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "narrative_draft"
    return "human_review_gate"


def human_review_gate(state: PharmacovigilanceState) -> PharmacovigilanceState:
    """HITL pause point. Graph compiles with interrupt_before=[human_review_gate]."""
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state, "Awaiting qualified reviewer causality/seriousness sign-off",
                 "human_review_gate"),
        "actor": "system",
        "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: PharmacovigilanceState) -> PharmacovigilanceState:
    """
    Submit the ICSR to the safety database (HIGH-RISK write) ONLY with a verified
    human approval bound at the gateway. Without approval the gateway returns
    PENDING and no case is filed.
    """
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")
    import datetime as dt
    try:
        res = gateway_tools.submit_report(
            claims,
            {
                "case_id": state.get("case_id"),
                "meddra_pt": state.get("meddra_pt"),
                "suspect_drug": state.get("suspect_drug"),
                "is_serious": state.get("is_serious"),
                "narrative_len": len(state.get("narrative_text", "")),
            },
            approval=approval,
        )
        if getattr(res, "allowed", False):
            state["submission_case_id"] = res.result.get("case_id", "ICSR-SUBMITTED-PENDING")
            state["case_status"] = "SUBMITTED"
            clock = state.get("reporting_clock_days")
            if clock:
                deadline = (
                    dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=clock)
                ).date().isoformat()
                state["reporting_deadline"] = deadline
        else:
            state["case_status"] = "PENDING"
    except Exception as exc:
        state.setdefault("errors", []).append(
            {"step": "finalize", "error": str(exc), "timestamp": _now(), "recoverable": True}
        )
        state["case_status"] = "PENDING"

    state["audit_trail"].append({
        **_audit(state, "Finalized ICSR — audit trail locked", "finalize"),
        "human_review_required": True,
        "actor": state.get("acting_user_claims", {}).get("sub", "system"),
    })
    state["completed_steps"].append("finalize")
    return state
