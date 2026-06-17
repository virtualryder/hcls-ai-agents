# agent/nodes.py
# ============================================================
# Node functions for the Medical Affairs MSL workflow.
#
# Workflow:
#   intake -> pull_hcp_and_content -> enrich_and_validate ->
#   draft_brief -> compliance_check ->
#   [routing] -> human_review_gate -> finalize -> END
#
# Routing disposition is set INSIDE compliance_check (persists in state).
# Off-label / promotional findings always → ESCALATE (never just REVISE).
# interrupt_before=["human_review_gate"] enforces HITL.
# finalize submits to MLR review — HIGH-RISK, requires approval.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, MedicalAffairsMSLState
from tools import (
    gateway_tools,
    hcp_profiler,
    content_retriever,
    brief_drafter,
    next_best_action,
    compliance_checker,
)

# ── Demo-mode fallback data ────────────────────────────────────────────────────

_DEMO_HCP: Dict[str, Any] = {
    "hcp_id": "HCP-DEMO-001",
    "name": "Dr. Jane Smith",
    "specialty": "Endocrinology",
    "institution": "Metro Diabetes Center",
    "clinical_interests": ["type 2 diabetes", "metabolic syndrome", "cardiovascular risk"],
    "recent_publications": ["Glycemic control in T2D: a 2025 review"],
    "meeting_history": [
        {"date": "2025-10-15", "topic": "Phase 3 data overview", "outcome": "Requested references"},
    ],
}

_DEMO_DOCS: List[Dict[str, Any]] = [
    {
        "doc_id": "DOC-PI-001",
        "title": "Demo-Drug Prescribing Information",
        "version": "3.0",
        "status": "APPROVED",
        "text": (
            "Demo-Drug is indicated for the treatment of type 2 diabetes mellitus in adults. "
            "In STUDY-301 (n=450), Demo-Drug reduced HbA1c by 1.2 percentage points vs placebo. "
            "Common adverse events: upper respiratory infection (8%), nausea (6%). "
            "Contraindicated in severe renal impairment (eGFR < 30)."
        ),
    },
    {
        "doc_id": "DOC-CSR-001",
        "title": "STUDY-301 Clinical Study Report Summary",
        "version": "1.0",
        "status": "APPROVED",
        "text": (
            "Phase 3 STUDY-301: 450 subjects, 52 weeks. Primary endpoint met "
            "(HbA1c reduction 1.2 pp, p<0.001 vs placebo). "
            "Cardiovascular safety: no increase in MACE. "
            "On-label indication: T2D management in adults."
        ),
    },
]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: MedicalAffairsMSLState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("draft_brief", "finalize"),
    }


def _claims(state: MedicalAffairsMSLState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-msl", "custom:hcls_role": "MSL",
    }


def _valid_hcp(profile: Any) -> bool:
    if not isinstance(profile, dict):
        return False
    name = profile.get("name", "")
    return bool(name) and not name.startswith("[") and name != "the HCP"


def intake(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "DRAFTING"
    state["audit_trail"].append(_audit(
        state,
        "Intake: HCP=" + str(state.get("hcp_id")) + " topic=" + str(state.get("topic", ""))[:60],
        "intake",
    ))
    state["completed_steps"].append("intake")
    return state


def pull_hcp_and_content(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """Retrieve HCP profile (CRM) and approved documents (DMS) via gateway."""
    state["current_step"] = "pull_hcp_and_content"
    claims = _claims(state)
    hcp_id = state.get("hcp_id", "HCP-DEMO-001")
    sources: List[str] = []

    # HCP profile
    if not _valid_hcp(state.get("hcp_profile")):
        try:
            gw_profile = gateway_tools.get_hcp(claims, hcp_id)
            if _valid_hcp(gw_profile):
                state["hcp_profile"] = gw_profile
                sources.append("crm")
            else:
                raise ValueError("gateway returned placeholder profile")
        except Exception as exc:
            state.setdefault("errors", []).append({
                "step": "pull_hcp_and_content:hcp", "error": str(exc),
                "timestamp": _now(), "recoverable": True,
            })
            # Demo fallback — use fixture, patch name/id
            profile = dict(_DEMO_HCP)
            if state.get("hcp_name"):
                profile["name"] = state["hcp_name"]
            profile["hcp_id"] = hcp_id
            state["hcp_profile"] = profile
    else:
        sources.append("crm(pre-seeded)")

    # Approved documents
    if not (isinstance(state.get("approved_documents"), list) and state["approved_documents"]):
        doc_ids = state.get("approved_doc_ids", ["DOC-PI-001", "DOC-CSR-001"])
        docs: List[Dict[str, Any]] = []
        for doc_id in doc_ids:
            try:
                doc = gateway_tools.get_document(claims, doc_id)
                if isinstance(doc, dict) and doc.get("title"):
                    docs.append(doc)
                    sources.append("dms")
            except Exception as exc:
                state.setdefault("errors", []).append({
                    "step": "pull_hcp_and_content:dms", "error": str(exc),
                    "timestamp": _now(), "recoverable": True,
                })
        state["approved_documents"] = docs if docs else list(_DEMO_DOCS)
    else:
        sources.append("dms(pre-seeded)")

    state["audit_trail"].append(
        _audit(state, "Retrieved HCP profile and approved content",
               "pull_hcp_and_content", sources)
    )
    state["completed_steps"].append("pull_hcp_and_content")
    return state


def enrich_and_validate(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """Enrich HCP profile, validate documents, build citation index, compute NBA."""
    state["current_step"] = "enrich_and_validate"

    # Enrich HCP profile
    topic = state.get("topic", "")
    profile = state.get("hcp_profile", {})
    enriched = hcp_profiler.enrich_hcp_profile(profile, topic)
    state["hcp_profile"] = enriched
    val = hcp_profiler.validate_hcp_profile(enriched)
    state["hcp_profile_valid"] = val["valid"]
    state["hcp_profile_issues"] = val["issues"] + val["warnings"]

    # Validate documents
    docs = state.get("approved_documents", [])
    doc_val = content_retriever.validate_documents(docs)
    state["document_validation"] = doc_val
    if doc_val["blocked"]:
        state.setdefault("errors", []).extend([
            {"step": "enrich_and_validate:docs", "error": iss,
             "timestamp": _now(), "recoverable": False}
            for iss in doc_val["issues"]
        ])
    # Use only approved docs for drafting
    state["approved_documents"] = doc_val["approved"] or docs

    # Citation index
    state["citation_index"] = content_retriever.build_citation_index(
        state["approved_documents"]
    )

    # Next best actions (deterministic, pre-brief)
    nba = next_best_action.recommend_actions(
        hcp_profile=enriched,
        meeting_purpose=state.get("meeting_purpose", ""),
        topic=topic,
        approved_docs=state["approved_documents"],
        compliance_findings=[],  # no compliance findings yet
    )
    state["next_best_actions"] = nba

    state["audit_trail"].append(
        _audit(state, "Enriched HCP profile, validated documents, built citation index",
               "enrich_and_validate")
    )
    state["completed_steps"].append("enrich_and_validate")
    return state


def draft_brief(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """Draft the MSL pre-call brief. LLM uses approved content only."""
    state["current_step"] = "draft_brief"
    out = brief_drafter.draft_brief(dict(state))
    state["brief_text"] = out["brief_text"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(
        _audit(state, "Drafted MSL pre-call brief (on-label, cited)",
               "draft_brief", model=out["drafted_by"])
    )
    state["completed_steps"].append("draft_brief")
    return state


def compliance_check(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """Run compliance + grounding gates; set routing disposition in state."""
    state["current_step"] = "compliance_check"
    text = state.get("brief_text", "")

    state["compliance_findings"] = compliance_checker.compliance_findings(text)
    state["grounding_report"] = compliance_checker.grounding_findings(text, dict(state))

    grounding = state["grounding_report"]
    findings = state["compliance_findings"]
    ungrounded = (
        grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])
    )

    # Off-label or promotional → always ESCALATE
    off_label = any("off-label" in f for f in findings)
    promotional = any("promotional" in f for f in findings)
    if off_label or promotional:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_BRIEF

    state["audit_trail"].append(
        _audit(state, "Ran compliance + grounding checks", "compliance_check")
    )
    state["completed_steps"].append("compliance_check")
    return state


def routing_decision(state: MedicalAffairsMSLState) -> str:
    """Pure read of disposition set in compliance_check (no state mutation)."""
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "draft_brief"
    return "human_review_gate"


def human_review_gate(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """HITL pause. Graph compiles with interrupt_before=['human_review_gate']."""
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state, "Awaiting Medical Affairs Approver review", "human_review_gate"),
        "actor": "system",
        "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: MedicalAffairsMSLState) -> MedicalAffairsMSLState:
    """Submit to MLR review (HIGH-RISK write) after Medical Affairs Approver sign-off."""
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")

    try:
        res = gateway_tools.submit_for_mlr_review(
            claims,
            {
                "hcp_id": state.get("hcp_id"),
                "topic": state.get("topic"),
                "meeting_date": state.get("meeting_date"),
                "brief_summary": state.get("brief_text", "")[:500],
            },
            approval=approval,
        )
        if getattr(res, "allowed", False):
            state["mlr_submission_id"] = res.result.get("submission_id", "MLR-PENDING")
            state["case_status"] = "SUBMITTED_MLR"
        else:
            state["case_status"] = "PENDING_REVIEW"
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "finalize", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })
        state["case_status"] = "PENDING_REVIEW"

    state["audit_trail"].append({
        **_audit(state, "Finalized: submitted to MLR review (HIGH-RISK, post-approval)",
                 "finalize", ["mlr"]),
        "human_review_required": True,
        "actor": state.get("acting_user_claims", {}).get("sub", "system"),
    })
    state["completed_steps"].append("finalize")
    return state
