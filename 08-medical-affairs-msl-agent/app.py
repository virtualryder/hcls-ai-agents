"""
Medical Affairs MSL Agent — Streamlit demo dashboard.

Full multi-tab workflow: intake HCP meeting request, pull CRM profile and
approved documents, enrich and validate, draft on-label pre-call brief,
run compliance checks (off-label, promotional, grounding), present to a
Medical Affairs Approver for sign-off, then submit to MLR review.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "platform_core"))

from agent.graph import build_medical_affairs_msl_graph
from agent.state import RecommendedAction

st.set_page_config(
    page_title="Medical Affairs MSL Agent",
    page_icon="💊",
    layout="wide",
)

ROLES = ["MSL", "MEDICAL_AFFAIRS_APPROVER"]


def load_meetings():
    f = HERE / "data" / "fixtures" / "sample_hcp_meetings.json"
    return json.loads(f.read_text())["meetings"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("💊 Medical Affairs MSL Agent")
st.sidebar.caption(
    "AI-assisted MSL briefs — Medical Affairs Approver reviews all content. "
    "On-label only. MLR submission requires explicit Approver sign-off."
)
role = st.sidebar.selectbox("Acting role (from your IdP)", ROLES, index=0)
user_sub = st.sidebar.text_input("User ID", value="demo.msl")
os.environ.setdefault("EXTRACT_MODE", "demo")
st.sidebar.info(
    f"Mode: **{os.getenv('EXTRACT_MODE', 'demo')}** · "
    f"Connectors: **{os.getenv('CONNECTOR_MODE', 'fixture')}**"
)

meetings = load_meetings()
labels = [
    f"{m['request_id']} — {m['hcp_name']} ({m['topic'][:45]})"
    for m in meetings
]
choice = st.sidebar.selectbox(
    "HCP meeting", range(len(meetings)), format_func=lambda i: labels[i]
)
meeting = meetings[choice]

st.title("MSL Pre-Call Brief Workflow")
st.write(
    f"**{meeting['hcp_name']}** · {meeting['topic']} · {meeting['meeting_date']}"
)
st.caption(meeting.get("meeting_purpose", ""))

(tab_run, tab_hcp, tab_docs, tab_compliance, tab_audit) = st.tabs([
    "Brief & Review",
    "HCP Profile",
    "Approved Documents",
    "Compliance & Grounding",
    "Audit Trail",
])

if "msl_result" not in st.session_state:
    st.session_state.msl_result = None

with tab_run:
    if st.button("▶ Run MSL brief workflow", type="primary"):
        seed = {
            k: meeting[k]
            for k in (
                "request_id", "hcp_id", "hcp_name", "topic",
                "meeting_date", "meeting_purpose", "instructions",
            )
        }
        seed["acting_user_claims"] = {"sub": user_sub, "custom:hcls_role": role}
        seed["hcp_profile"] = meeting.get("hcp_profile", {})
        seed["approved_documents"] = meeting.get("approved_documents", [])
        graph = build_medical_affairs_msl_graph(use_memory=False)
        with st.spinner("Drafting compliant MSL brief…"):
            st.session_state.msl_result = graph.invoke(seed)

    res = st.session_state.msl_result
    if res:
        action = res.get("recommended_action")
        color = {
            RecommendedAction.APPROVE_BRIEF: "green",
            RecommendedAction.REVISE: "orange",
            RecommendedAction.ESCALATE: "red",
        }.get(action, "gray")
        st.markdown(
            f"**Disposition:** :{color}[{getattr(action, 'value', action)}] · "
            f"drafted by `{res.get('drafted_by')}` · "
            f"status `{res.get('case_status')}`"
        )

        if action == RecommendedAction.ESCALATE:
            st.error(
                "ESCALATED: Compliance issue detected. "
                "This brief must NOT be used with HCPs until resolved by a Medical Affairs Approver."
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            g = res.get("grounding_report", {})
            st.metric("Grounded (all claims cited)", "✅ yes" if g.get("grounded") else "⚠ review")
        with col2:
            nf = len(res.get("compliance_findings", []))
            st.metric("Compliance findings", nf)
        with col3:
            dv = res.get("document_validation", {})
            blocked = len(dv.get("blocked", []))
            st.metric("Blocked documents", blocked)

        st.subheader("MSL Pre-Call Brief")
        st.write(res.get("brief_text", ""))

        if res.get("compliance_findings"):
            st.subheader("Compliance Issues")
            for f in res["compliance_findings"]:
                st.error(f)

        st.divider()
        st.subheader("👤 Human Review Gate (Medical Affairs Approver)")
        if role != "MEDICAL_AFFAIRS_APPROVER":
            st.info(
                "Switch acting role to MEDICAL_AFFAIRS_APPROVER to review the brief, "
                "confirm on-label compliance, and authorize MLR submission."
            )
        else:
            st.checkbox(
                "I have reviewed the brief for on-label compliance, citation accuracy, "
                "and grounding. No off-label or promotional content is present."
            )
            if action == RecommendedAction.ESCALATE:
                st.error(
                    "This brief has a compliance escalation. Resolve the finding before approving."
                )
            elif st.button("✅ Approve & submit to MLR review"):
                st.success(
                    "Medical Affairs Approver sign-off recorded with your verified identity. "
                    "In a live deployment the gateway mints a scoped token and submits the "
                    "brief to the MLR system (audited, HIGH-RISK write)."
                )
    else:
        st.info("Select an HCP meeting and click 'Run MSL brief workflow'.")

with tab_hcp:
    res = st.session_state.msl_result
    if res:
        st.subheader("HCP Profile (Enriched)")
        prof = res.get("hcp_profile", meeting.get("hcp_profile", {}))
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Specialty", prof.get("specialty", "N/A"))
            st.metric("Engagement tier", prof.get("engagement_tier", prof.get("tier", "N/A")))
            st.metric("Prior interactions", prof.get("prior_interaction_count", 0))
        with col2:
            st.metric("Institution", prof.get("institution", "N/A"))
            interests = prof.get("relevant_interests") or prof.get("clinical_interests", [])
            st.write("**Clinical interests (relevant):**")
            for i in interests[:5]:
                st.markdown(f"- {i}")
        if res.get("hcp_profile_issues"):
            for iss in res["hcp_profile_issues"]:
                st.warning(iss)
        st.subheader("Meeting history")
        hist = prof.get("meeting_history", [])
        if hist:
            st.dataframe(hist, use_container_width=True)
        else:
            st.info("No prior meeting history.")
    else:
        st.subheader("HCP Profile (from fixture)")
        st.json(meeting.get("hcp_profile", {}))

with tab_docs:
    res = st.session_state.msl_result
    docs = (res.get("approved_documents") if res else None) or meeting.get("approved_documents", [])
    doc_val = res.get("document_validation", {}) if res else {}

    st.subheader("Approved Documents")
    if doc_val.get("blocked"):
        for b in doc_val["blocked"]:
            st.error(f"BLOCKED: {b.get('title', b.get('doc_id'))} — status: {b.get('status')}")
    for d in docs:
        with st.expander(f"{d.get('title')} (v{d.get('version', 'N/A')}) — {d.get('status')}"):
            st.caption(d.get("text", ""))

    if res and res.get("citation_index"):
        st.subheader("Citation Index")
        st.json(res["citation_index"])

    if res and res.get("next_best_actions"):
        st.subheader("Next Best Actions")
        nba = res["next_best_actions"]
        for act in nba.get("follow_up_actions", []):
            st.markdown(f"- {act}")

with tab_compliance:
    res = st.session_state.msl_result
    if res:
        st.subheader("Compliance Check")
        findings = res.get("compliance_findings", [])
        if not findings:
            st.success("No compliance issues found.")
        else:
            for f in findings:
                st.error(f)

        st.subheader("Grounding Report")
        g = res.get("grounding_report", {})
        st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review required")
        if not g.get("grounded"):
            st.warning(
                f"Ungrounded numbers: {g.get('ungrounded_numbers')}\n\n"
                f"Ungrounded entities: {g.get('ungrounded_entities')}"
            )
        st.json(g)
    else:
        st.info("Run the workflow to see compliance results.")

with tab_audit:
    res = st.session_state.msl_result
    if res and res.get("audit_trail"):
        st.subheader("Audit Trail")
        st.dataframe(res["audit_trail"], use_container_width=True)
    else:
        st.info("Run the workflow to populate the audit trail.")

st.caption(
    "Decision-support tool for Medical Science Liaisons. "
    "All AI output requires review by a Medical Affairs Approver. "
    "On-label content only. MLR submission requires explicit Approver sign-off."
)
