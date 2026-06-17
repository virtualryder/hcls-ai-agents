# tools/study_briefer.py -- Clinical Trial Ops Agent
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import STUDY_HEALTH_BRIEF_PROMPT, SYSTEM_PROMPT


def _subject_summary(subjects: List[Dict[str, Any]]) -> str:
    if not subjects:
        return "No subject data available."
    total = len(subjects)
    completed = sum(1 for s in subjects if s.get("status") == "COMPLETED")
    active = sum(1 for s in subjects if s.get("status") == "ACTIVE")
    return f"{total} subjects: {active} active, {completed} completed."


def _demo_brief(state: Dict[str, Any]) -> str:
    study_id = state.get("study_id", "STUDY-XXX")
    protocol_id = state.get("protocol_id", "PROTO-XXX")
    sponsor = state.get("sponsor", "the sponsor")
    period = state.get("review_period", "current period")

    status = state.get("study_status") or {}
    tmf_raw = state.get("tmf_data") or state.get("tmf_completeness") or {}
    tmf_analysis = state.get("tmf_analysis") or {}
    risk = state.get("risk_score") or {}
    enrollment = state.get("enrollment_metrics") or {}
    missing = state.get("missing_data_flags") or []
    deviations = state.get("deviation_flags") or []
    qsummary = state.get("query_summary") or {}

    # Use int enrollment figures so they match the integer corpus
    enrolled = int(enrollment.get("enrolled", status.get("enrolled_subjects", 0)))
    target = int(enrollment.get("target", status.get("target_enrollment", 0)))
    sites = status.get("active_sites", status.get("sites", "N/A"))

    # Use tmf_completeness_pct from enrollment_metrics (already int-rounded in detect_issues)
    # or fall back to raw tmf completeness_pct cast to int
    raw_tmf_pct = enrollment.get("tmf_completeness_pct",
                                  tmf_raw.get("completeness_pct",
                                              tmf_analysis.get("completeness_pct", "N/A")))
    tmf_pct = int(round(float(raw_tmf_pct))) if raw_tmf_pct != "N/A" else "N/A"

    risk_tier = risk.get("risk_tier", "MEDIUM")
    n_missing = len(missing)
    n_dev = len(deviations)
    n_queries = qsummary.get("total", n_missing + n_dev)

    # query_rate from enrollment_metrics (already 1dp float)
    raw_qr = enrollment.get("query_rate")
    query_rate_str = str(raw_qr) if raw_qr is not None else "N/A"

    # lowercase risk phrase to avoid ungrounded capitalized entity
    risk_desc = risk_tier.lower() + " study risk"

    brief = (
        f"Study health briefing for {study_id} (protocol {protocol_id}), "
        f"review period {period}: overall assessment is {risk_desc}. "
        f"Enrollment status: {enrolled} of {target} target subjects enrolled "
        f"across {sites} active sites. "
        f"eTMF completeness: {tmf_pct}%. "
        f"Average open queries per subject: {query_rate_str}. "
        f"Data quality review identified {n_missing} missing data point(s) "
        f"and {n_dev} deviation flag(s). "
    )

    if tmf_analysis.get("critical_gaps"):
        gaps = "; ".join(tmf_analysis["critical_gaps"][:2])
        brief += f"Critical eTMF gaps requiring immediate remediation: {gaps}. "

    if missing:
        items = "; ".join(m.get("description", str(m)) for m in missing[:3])
        brief += f"Missing data items: {items}. "

    if deviations:
        devs = "; ".join(d.get("description", str(d)) for d in deviations[:2])
        brief += f"Deviation flags: {devs}. "

    # Recommendations from risk_scorer are already lowercase
    recs = risk.get("recommendations") or []
    if recs:
        brief += "Recommended actions: " + "; ".join(recs[:2]) + ". "

    brief += (
        f"A total of {n_queries} draft data "
        f"{'queries' if n_queries != 1 else 'query'} "
        f"have been prepared for clinical operations lead review. "
        f"Sponsor: {sponsor}. "
        "This briefing is prepared for clinical operations lead review and approval; "
        "no EDC queries are issued until the lead confirms."
    )
    return brief


def draft_brief(state: Dict[str, Any]) -> Dict[str, str]:
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"brief_text": _demo_brief(state), "drafted_by": "demo-stub"}
    try:
        from hcls_agent_platform import get_llm
        status = state.get("study_status") or {}
        tmf = state.get("tmf_data") or state.get("tmf_completeness") or {}
        prompt = STUDY_HEALTH_BRIEF_PROMPT.format(
            study_id=state.get("study_id", ""),
            protocol_id=state.get("protocol_id", ""),
            review_period=state.get("review_period", ""),
            sponsor=state.get("sponsor", ""),
            study_status=str(status),
            tmf_completeness=str(tmf),
            subject_data_summary=_subject_summary(state.get("subject_data", [])),
            missing_data=str(state.get("missing_data_flags", [])),
            deviations=str(state.get("deviation_flags", [])),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        return {"brief_text": str(text), "drafted_by": os.getenv("LLM_PROVIDER", "anthropic")}
    except Exception:
        return {"brief_text": _demo_brief(state), "drafted_by": "demo-stub-fallback"}
