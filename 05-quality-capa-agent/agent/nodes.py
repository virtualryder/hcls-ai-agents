# agent/nodes.py
from __future__ import annotations
import datetime as _dt, sys
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, QualityCAPAState
from tools import gateway_tools, complaint_classifier, similarity_search, root_cause_analyzer, capa_drafter, quality_checker


def _now(): return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state, action, node, sources=None, model=""):
    return {"timestamp": _now(), "actor": "ai_agent", "action": action, "node": node,
            "data_sources_accessed": sources or [], "ai_model_used": model,
            "human_review_required": node in ("draft_capa", "finalize")}


def _claims(state):
    return state.get("acting_user_claims") or {"sub": "demo-qa", "custom:hcls_role": "QUALIFIED_PERSON"}


def intake(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "CLASSIFYING"
    state["audit_trail"].append(_audit(state, f"Intake of {state.get('event_type','quality event')} {state.get('complaint_id')}", "intake"))
    state["completed_steps"].append("intake")
    return state


def classify_event(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "classify_event"
    claims = _claims(state)
    complaint_id = state.get("complaint_id", "COMP-DEMO-001")
    sources: List[str] = []
    try:
        record = gateway_tools.get_complaint(claims, complaint_id)
        if isinstance(record, dict) and record:
            state["complaint_record"] = {
                "complaint_id": complaint_id,
                "event_type": state.get("event_type", record.get("event_type", "COMPLAINT")),
                "product": state.get("product", record.get("product", "Demo-Product")),
                "lot_number": state.get("lot_number", "LOT-2026-001"),
                "site": state.get("site", "SITE-MFG-01"),
                "description": state.get("description", "Quality event."),
                "severity": state.get("severity", record.get("severity", "MAJOR")),
                "reported_date": "2026-01-15",
            }
            sources.append("qms")
    except Exception as exc:
        state.setdefault("errors", []).append({"step": "classify_event", "error": str(exc), "timestamp": _now(), "recoverable": True})
    state.setdefault("complaint_record", {
        "complaint_id": complaint_id,
        "event_type": state.get("event_type", "COMPLAINT"),
        "product": state.get("product", "Demo-Product"),
        "lot_number": state.get("lot_number", "LOT-2026-001"),
        "site": state.get("site", "SITE-MFG-01"),
        "description": state.get("description", "Quality event description."),
        "severity": state.get("severity", "MAJOR"),
        "reported_date": "2026-01-15",
    })
    state["classification"] = complaint_classifier.classify(
        description=state.get("description", ""),
        declared_severity=state.get("severity", ""),
        declared_type=state.get("event_type", ""),
    )
    state["audit_trail"].append(_audit(state, "Classified quality event (severity, risk, regulatory obligation)", "classify_event", sources))
    state["completed_steps"].append("classify_event")
    return state


def search_similar_events(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "search_similar_events"
    claims = _claims(state)
    sources: List[str] = []
    similar: List[Dict[str, Any]] = []
    try:
        result = gateway_tools.search_similar(claims, {"product": state.get("product"), "event_type": state.get("event_type"), "description": state.get("description", "")})
        if isinstance(result, list):
            similar = result
        elif isinstance(result, dict):
            m = result.get("matches", [])
            similar = m if isinstance(m, list) else []
        sources.append("qms")
    except Exception as exc:
        state.setdefault("errors", []).append({"step": "search_similar_events", "error": str(exc), "timestamp": _now(), "recoverable": True})
    if not similar:
        similar = similarity_search.search_similar_demo({"product": state.get("product",""), "event_type": state.get("event_type",""), "description": state.get("description","")})
    state["similar_events"] = similar
    clusters = similarity_search.cluster_events(similar)
    state["clusters"] = clusters
    state["audit_trail"].append(_audit(state, f"Searched similar events ({len(similar)} found); clustered into {len(clusters)} group(s)", "search_similar_events", sources))
    state["completed_steps"].append("search_similar_events")
    return state


def root_cause_analysis(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "root_cause_analysis"
    result = root_cause_analyzer.analyze(description=state.get("description",""), similar_events=state.get("similar_events",[]), clusters=state.get("clusters",[]))
    state["root_cause_hypotheses"] = result["root_cause_hypotheses"]
    cls = state.get("classification", {})
    cls["ishikawa_categories"] = result["ishikawa_categories"]
    cls["recurrence_risk"] = result["recurrence_risk"]
    cls["investigation_method"] = result["investigation_method"]
    state["classification"] = cls
    state["audit_trail"].append(_audit(state, f"Root cause analysis: {len(result['root_cause_hypotheses'])} hypothesis(es); recurrence risk={result['recurrence_risk']}", "root_cause_analysis"))
    state["completed_steps"].append("root_cause_analysis")
    return state


def draft_capa(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "draft_capa"
    out = capa_drafter.draft_capa(dict(state))
    state["capa_plan"] = out["capa_plan"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(_audit(state, "Drafted CAPA plan (LLM-assisted; QP review required)", "draft_capa", model=out["drafted_by"]))
    state["completed_steps"].append("draft_capa")
    return state


def quality_check(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "quality_check"
    text = state.get("capa_plan", "")
    state["quality_findings"] = quality_checker.quality_findings(text)
    state["grounding_report"] = quality_checker.grounding_findings(text, dict(state))
    grounding = state.get("grounding_report", {})
    findings = state.get("quality_findings", [])
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])
    cls = state.get("classification", {})
    critical = cls.get("risk_level") == "HIGH"
    reg_reporting = cls.get("regulatory_reporting_required", False)
    if critical and reg_reporting and any("regulatory" in f for f in findings):
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_CAPA
    state["audit_trail"].append(_audit(state, f"Quality check: {len(findings)} finding(s); grounded={grounding.get('grounded', True)}; action={state['recommended_action'].value}", "quality_check"))
    state["completed_steps"].append("quality_check")
    return state


def routing_decision(state: QualityCAPAState) -> str:
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "draft_capa"
    return "human_review_gate"


def human_review_gate(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    entry = _audit(state, "Awaiting Qualified Person review and approval of CAPA plan", "human_review_gate")
    entry["actor"] = "system"
    entry["human_review_required"] = True
    state["audit_trail"].append(entry)
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: QualityCAPAState) -> QualityCAPAState:
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")
    try:
        res = gateway_tools.create_capa_draft(claims, {
            "complaint_id": state.get("complaint_id"), "product": state.get("product"),
            "event_type": state.get("event_type"), "severity": state.get("severity"),
            "plan_summary": state.get("capa_plan", "")[:500],
        }, approval=approval)
        if getattr(res, "allowed", False):
            state["capa_draft_id"] = res.result.get("capa_id", "CAPA-DRAFT-PENDING")
            state["case_status"] = "CAPA_CREATED"
        else:
            state["case_status"] = "PENDING_REVIEW"
    except Exception as exc:
        state.setdefault("errors", []).append({"step": "finalize", "error": str(exc), "timestamp": _now(), "recoverable": True})
        state["case_status"] = "PENDING_REVIEW"
    entry = _audit(state, "Finalized: CAPA draft creation attempted (post QP approval)", "finalize", ["qms"])
    entry["human_review_required"] = True
    entry["actor"] = state.get("acting_user_claims", {}).get("sub", "system")
    state["audit_trail"].append(entry)
    state["completed_steps"].append("finalize")
    return state
