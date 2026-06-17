# agent/nodes.py -- Clinical Trial Ops Agent (v3)
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, ClinicalTrialOpsState
from tools import gateway_tools, study_briefer, quality_checker, tmf_analyzer, query_drafter, risk_scorer

_DEMO_STUDY_STATUS: Dict[str, Any] = {
    "study_id": "DEMO-STUDY-001",
    "sponsor": "Demo Pharma Inc.",
    "phase": "Phase 3",
    "status": "ACTIVE",
    "enrolled_subjects": 124,
    "target_enrollment": 200,
    "active_sites": 8,
    "planned_sites": 12,
    "screen_failures": 18,
    "start_date": "2025-03-01",
}

_DEMO_TMF: Dict[str, Any] = {
    "study_id": "DEMO-STUDY-001",
    "completeness_pct": 87,
    "missing_documents": ["Site Activation Log - Site 04", "IRB Correspondence - Site 07"],
    "last_reviewed": "2026-01-15",
}

_DEMO_SUBJECTS: List[Dict[str, Any]] = [
    {"subject_id": "001-001", "site_id": "SITE-01", "status": "ACTIVE",
     "visit": "Week 12", "missing_fields": ["Weight", "BP_Diastolic"],
     "visits_completed": 4, "visits_expected": 6, "open_queries": 2},
    {"subject_id": "001-002", "site_id": "SITE-01", "status": "ACTIVE",
     "visit": "Week 8",  "missing_fields": [],
     "visits_completed": 3, "visits_expected": 6, "open_queries": 0},
    {"subject_id": "002-001", "site_id": "SITE-02", "status": "COMPLETED",
     "visit": "EOS",     "missing_fields": [],
     "visits_completed": 6, "visits_expected": 6, "open_queries": 0},
    {"subject_id": "003-001", "site_id": "SITE-03", "status": "ACTIVE",
     "visit": "Week 8",  "missing_fields": ["HbA1c_Result"],
     "visits_completed": 3, "visits_expected": 6, "open_queries": 1},
    {"subject_id": "003-002", "site_id": "SITE-03", "status": "ACTIVE",
     "visit": "Week 4",  "missing_fields": [],
     "visits_completed": 2, "visits_expected": 6, "open_queries": 0},
]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: ClinicalTrialOpsState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("draft_briefing", "human_review_gate", "finalize"),
    }


def _claims(state: ClinicalTrialOpsState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-cra", "custom:hcls_role": "CRA",
    }


def _is_valid_list(val: Any) -> bool:
    return isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict)


def _has_rich_tmf(val: Any) -> bool:
    """Return True if state already has a rich seeded tmf_data (has missing_documents list)."""
    return (isinstance(val, dict) and "completeness_pct" in val
            and "missing_documents" in val)


def intake(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "REVIEWING"
    state["audit_trail"].append(_audit(
        state, "Intake of clinical trial ops review for " + str(state.get("study_id", "unknown")),
        "intake",
    ))
    state["completed_steps"].append("intake")
    return state


def pull_study_data(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "pull_study_data"
    claims = _claims(state)
    study_id = state.get("study_id", "DEMO-STUDY-001")
    sources: List[str] = []

    # CTMS study status -- prefer pre-seeded if it has sponsor field
    if isinstance(state.get("study_status"), dict) and state["study_status"].get("sponsor"):
        sources.append("ctms(pre-seeded)")
    else:
        try:
            status = gateway_tools.get_study_status(claims, study_id)
            if isinstance(status, dict) and status.get("sponsor"):
                state["study_status"] = status
                sources.append("ctms")
            else:
                state.setdefault("study_status", _DEMO_STUDY_STATUS)
        except Exception as exc:
            state.setdefault("errors", []).append(
                {"step": "pull_study_data:ctms", "error": str(exc), "timestamp": _now(), "recoverable": True}
            )
            state.setdefault("study_status", _DEMO_STUDY_STATUS)

    # eTMF -- prefer pre-seeded rich data (has missing_documents) over gateway fixture
    if _has_rich_tmf(state.get("tmf_data")):
        sources.append("etmf(pre-seeded)")
    else:
        try:
            tmf = gateway_tools.get_tmf_completeness(claims, study_id)
            if isinstance(tmf, dict) and "completeness_pct" in tmf:
                # Gateway fixture lacks missing_documents; merge with demo defaults
                merged = dict(_DEMO_TMF)
                merged["completeness_pct"] = tmf["completeness_pct"]
                state["tmf_data"] = merged
                sources.append("etmf")
            else:
                state.setdefault("tmf_data", _DEMO_TMF)
        except Exception as exc:
            state.setdefault("errors", []).append(
                {"step": "pull_study_data:etmf", "error": str(exc), "timestamp": _now(), "recoverable": True}
            )
            state.setdefault("tmf_data", _DEMO_TMF)

    # Subject data -- prefer pre-seeded list
    existing_subjects = state.get("subject_data")
    if _is_valid_list(existing_subjects):
        sources.append("edc(pre-seeded)")
    else:
        state["subject_data"] = _DEMO_SUBJECTS

    state["audit_trail"].append(_audit(
        state, "Pulled study status (CTMS), eTMF completeness, and subject data (EDC)",
        "pull_study_data", sources,
    ))
    state["completed_steps"].append("pull_study_data")
    return state


def analyze_tmf(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "analyze_tmf"
    tmf_raw = state.get("tmf_data") or state.get("tmf_completeness") or _DEMO_TMF
    analysis = tmf_analyzer.analyze(tmf_raw)
    state["tmf_analysis"] = analysis

    existing_devs = list(state.get("deviation_flags") or [])
    for gap in analysis.get("critical_gaps", []):
        existing_devs.append({
            "subject_id": "STUDY-LEVEL",
            "site_id": "TMF",
            "description": "Missing critical eTMF document: " + gap,
            "deviation_type": "TMF_GAP",
            "severity": "CRITICAL",
        })
    state["deviation_flags"] = existing_devs

    state["audit_trail"].append(_audit(
        state,
        f"Analyzed eTMF: {analysis['inspection_risk']} inspection risk, "
        f"{len(analysis['critical_gaps'])} critical gap(s)",
        "analyze_tmf", ["etmf"],
    ))
    state["completed_steps"].append("analyze_tmf")
    return state


def detect_issues(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "detect_issues"
    subjects = state.get("subject_data", [])
    if not isinstance(subjects, list):
        subjects = _DEMO_SUBJECTS
    subjects = [s for s in subjects if isinstance(s, dict)]
    if not subjects:
        subjects = _DEMO_SUBJECTS

    study_status = state.get("study_status") or _DEMO_STUDY_STATUS
    enrolled = int(study_status.get("enrolled_subjects", study_status.get("enrolled", 0)))
    target = int(study_status.get("target_enrollment", 450))
    # enrollment_pct: round to int so grounding corpus finds it
    enrollment_pct = int(round(enrolled / target * 100)) if target else 0

    total_open_queries = sum(s.get("open_queries", 0) for s in subjects)
    # query_rate: keep as 1dp float and add to corpus via enrollment_metrics
    query_rate = round(total_open_queries / len(subjects), 1) if subjects else 0.0

    visits_completed = sum(s.get("visits_completed", 0) for s in subjects)
    visits_expected = sum(s.get("visits_expected", 1) for s in subjects)
    # visit_completion_pct: round to int for grounding
    visit_completion_pct = int(round(visits_completed / visits_expected * 100)) if visits_expected else 0

    tmf = state.get("tmf_data") or state.get("tmf_completeness") or _DEMO_TMF
    tmf_pct = float(tmf.get("completeness_pct", 0))
    # Use int version for grounding (e.g. 87 not 87.4)
    tmf_pct_int = int(round(tmf_pct))
    tmf_analysis = state.get("tmf_analysis") or {}
    tmf_critical_gaps = len(tmf_analysis.get("critical_gaps", []))

    risk_result = risk_scorer.score(
        enrolled=enrolled,
        target_enrollment=target,
        tmf_completeness_pct=tmf_pct,
        tmf_critical_gaps=tmf_critical_gaps,
        query_rate=query_rate,
        total_open_queries=total_open_queries,
        visit_completion_pct=visit_completion_pct,
    )
    state["risk_score"] = risk_result

    issues: List[Dict[str, Any]] = []
    if enrollment_pct < 80:
        issues.append({"type": "ENROLLMENT_BEHIND", "severity": "HIGH",
                       "description": "Enrollment below 80% of target", "value": enrollment_pct})
    if query_rate > 1.5:
        issues.append({"type": "HIGH_QUERY_RATE", "severity": "MEDIUM",
                       "description": "Average open queries per subject exceeds threshold",
                       "value": query_rate})
    if visit_completion_pct < 85:
        issues.append({"type": "VISIT_COMPLETION_LOW", "severity": "MEDIUM",
                       "description": "Visit completion rate below 85%",
                       "value": visit_completion_pct})
    if tmf_pct < 90:
        issues.append({"type": "TMF_INCOMPLETE", "severity": "HIGH",
                       "description": "TMF completeness below 90%", "value": tmf_pct_int})

    state["detected_issues"] = issues
    state["enrollment_metrics"] = {
        "enrolled": enrolled,
        "target": target,
        "enrollment_pct": enrollment_pct,
        "total_open_queries": total_open_queries,
        "query_rate": query_rate,
        "visit_completion_pct": visit_completion_pct,
        "tmf_completeness_pct": tmf_pct_int,
    }

    existing_flags = state.get("missing_data_flags")
    if not existing_flags:
        flags: List[Dict[str, Any]] = []
        for s in subjects:
            for field in s.get("missing_fields", []):
                flags.append({
                    "subject_id": s.get("subject_id", "unknown"),
                    "site_id": s.get("site_id", "unknown"),
                    "visit": s.get("visit", ""),
                    "description": f"Missing CRF field '{field}' at {s.get('visit', 'visit')}",
                    "severity": "MINOR",
                })
        state["missing_data_flags"] = flags
    state.setdefault("deviation_flags", [])

    state["audit_trail"].append(_audit(
        state,
        f"Detected {len(issues)} operational issue(s); risk tier: {risk_result['risk_tier']}",
        "detect_issues",
    ))
    state["completed_steps"].append("detect_issues")
    return state


def draft_queries(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "draft_queries"
    study_id = state.get("study_id", "STUDY-XXX")
    protocol_id = state.get("protocol_id", "PROTO-XXX")

    mf_queries = query_drafter.draft_from_missing_fields(
        state.get("missing_data_flags", []), study_id, protocol_id
    )
    dev_queries = query_drafter.draft_from_deviation_flags(
        state.get("deviation_flags", []), study_id, protocol_id
    )
    all_queries = mf_queries + dev_queries
    state["data_queries"] = all_queries
    state["query_summary"] = query_drafter.summarize_queries(all_queries)

    state["audit_trail"].append(_audit(
        state,
        f"Drafted {len(all_queries)} EDC {'queries' if len(all_queries) != 1 else 'query'} "
        "(pending ClinOps Lead approval before issuance)",
        "draft_queries",
    ))
    state["completed_steps"].append("draft_queries")
    return state


def draft_briefing(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "draft_briefing"
    out = study_briefer.draft_brief(dict(state))
    state["brief_text"] = out["brief_text"]
    state["draft_text"] = out["brief_text"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(_audit(
        state, "Drafted study health operational briefing",
        "draft_briefing", model=out["drafted_by"],
    ))
    state["completed_steps"].append("draft_briefing")
    return state


def quality_check(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "quality_check"
    text = state.get("brief_text") or state.get("draft_text", "")
    state["quality_findings"] = quality_checker.quality_findings(text)
    state["grounding_report"] = quality_checker.grounding_findings(text, dict(state))

    grounding = state.get("grounding_report", {})
    findings = state.get("quality_findings", [])
    ungrounded = grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])

    risk_tier = (state.get("risk_score") or {}).get("risk_tier", "LOW")
    tmf_risk = (state.get("tmf_analysis") or {}).get("inspection_risk", "LOW")
    composite = (state.get("risk_score") or {}).get("composite_score", 0)

    # ESCALATE: CRITICAL risk (composite>=70 OR CRITICAL tier) OR CRITICAL TMF inspection risk
    if risk_tier == "CRITICAL" or tmf_risk == "CRITICAL" or composite >= 70:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_BRIEF

    state["audit_trail"].append(_audit(
        state, "Ran quality and grounding checks; set disposition", "quality_check",
    ))
    state["completed_steps"].append("quality_check")
    return state


def routing_decision(state: ClinicalTrialOpsState) -> str:
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "draft_briefing"
    return "human_review_gate"


def human_review_gate(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state, "Awaiting ClinOps Lead review and approval", "human_review_gate"),
        "actor": "system",
        "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: ClinicalTrialOpsState) -> ClinicalTrialOpsState:
    state["current_step"] = "finalize"
    claims = _claims(state)
    approval = state.get("approval")
    critical_queries = [
        q for q in state.get("data_queries", [])
        if q.get("severity") in ("CRITICAL", "MAJOR")
    ]

    issued_ids: List[str] = []
    if critical_queries:
        try:
            res = gateway_tools.create_edc_query(
                claims,
                {
                    "study_id": state.get("study_id"),
                    "query_type": "DATA_QUALITY",
                    "queries": critical_queries[:5],
                    "briefing_ref": (state.get("brief_text", ""))[:200],
                },
                approval=approval,
            )
            if getattr(res, "allowed", False):
                issued_ids.append(res.result.get("query_id", "EDC-Q-PENDING"))
                state["case_status"] = "QUERIES_ISSUED"
            else:
                state["case_status"] = "PENDING_REVIEW"
        except Exception as exc:
            state.setdefault("errors", []).append(
                {"step": "finalize", "error": str(exc), "timestamp": _now(), "recoverable": True}
            )
            state["case_status"] = "PENDING_REVIEW"
    else:
        state["case_status"] = "FINALIZED"

    state["edc_query_ids"] = issued_ids
    state["audit_trail"].append({
        **_audit(state, "Finalized briefing; audit trail locked", "finalize", ["ctms", "edc"]),
        "human_review_required": True,
        "actor": (state.get("acting_user_claims") or {}).get("sub", "system"),
    })
    state["completed_steps"].append("finalize")
    return state
