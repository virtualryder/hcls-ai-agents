"""
Clinical Trial Ops Agent -- Streamlit demo dashboard.

Full multi-tab dashboard mirroring flagship agent 02 depth:
  - Role selector (CRA / CLINOPS_LEAD / CTM)
  - Run workflow against any of the 3 fixture studies
  - Tabs: Briefing & Review | Issues & Queries | TMF Analysis | Risk Score | Audit Trail
  - HITL approval section visible only to CLINOPS_LEAD
  - Runs with no API key in EXTRACT_MODE=demo
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

from agent.graph import build_clinical_trial_ops_graph
from agent.state import RecommendedAction

st.set_page_config(
    page_title="Clinical Trial Ops Agent",
    page_icon="🔬",
    layout="wide",
)

ROLES = ["CRA", "CLINOPS_LEAD", "CTM"]


def load_studies():
    f = HERE / "data" / "fixtures" / "sample_studies.json"
    return json.loads(f.read_text())["studies"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔬 Clinical Trial Ops Agent")
st.sidebar.caption(
    "AI-assisted study monitoring — ClinOps Lead approves all EDC queries."
)
role = st.sidebar.selectbox("Acting role (from your IdP)", ROLES, index=0)
user_sub = st.sidebar.text_input("User ID", value="demo.clinops.user")
os.environ.setdefault("EXTRACT_MODE", "demo")
st.sidebar.info(
    f"Mode: **{os.getenv('EXTRACT_MODE', 'demo')}** · "
    f"Connectors: **{os.getenv('CONNECTOR_MODE', 'fixture')}**"
)

studies = load_studies()
labels = [
    f"{s['request_id']} — {s['study_id']} ({s.get('indication', '')})"
    for s in studies
]
choice = st.sidebar.selectbox(
    "Study review request", range(len(studies)), format_func=lambda i: labels[i]
)
study = studies[choice]

st.title("Clinical Trial Operations — Study Health Monitoring")
st.write(
    f"**{study['study_id']}** · {study['protocol_id']} · "
    f"{study.get('indication', '')} · Period: {study.get('review_period', '')}"
)

tab_brief, tab_issues, tab_tmf, tab_risk, tab_audit = st.tabs([
    "Briefing & Review",
    "Issues & Queries",
    "TMF Analysis",
    "Risk Score",
    "Audit Trail",
])

if "ct_result" not in st.session_state:
    st.session_state.ct_result = None

# ── Tab 1: Briefing & Review ──────────────────────────────────────────────────
with tab_brief:
    if st.button("▶ Run study health workflow", type="primary"):
        seed = {k: study[k] for k in study if k != "context"}
        graph = build_clinical_trial_ops_graph(use_memory=False)
        with st.spinner("Analyzing study data and drafting briefing…"):
            st.session_state.ct_result = graph.invoke(seed)

    res = st.session_state.ct_result
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

        col1, col2, col3 = st.columns(3)
        em = res.get("enrollment_metrics", {})
        with col1:
            pct = em.get("enrollment_pct", 0)
            st.metric(
                "Enrollment",
                f"{em.get('enrolled', 0)} / {em.get('target', 0)}",
                delta=f"{pct}% of target",
                delta_color="normal" if pct >= 80 else "inverse",
            )
        with col2:
            tmf_pct = em.get("tmf_completeness_pct", 0)
            st.metric(
                "eTMF Completeness",
                f"{tmf_pct}%",
                delta_color="normal" if tmf_pct >= 90 else "inverse",
            )
        with col3:
            rs = res.get("risk_score", {})
            tier = rs.get("risk_tier", "UNKNOWN")
            st.metric("Risk Tier", tier)

        g = res.get("grounding_report", {})
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review")
        with col5:
            qf = res.get("quality_findings", [])
            st.metric("Quality findings", len(qf))
            for f in qf:
                st.warning(f)

        st.subheader("Study Health Briefing")
        st.write(res.get("brief_text", ""))

        st.divider()
        st.subheader("👤 Human Review Gate (ClinOps Lead)")
        if role != "CLINOPS_LEAD":
            st.info(
                "Switch acting role to CLINOPS_LEAD to review and approve "
                "drafted EDC queries before they are issued to sites."
            )
        else:
            st.checkbox(
                "I have reviewed the study health briefing, all detected issues, "
                "TMF analysis, risk score, and drafted queries."
            )
            n_queries = len(res.get("data_queries", []))
            n_critical = res.get("query_summary", {}).get("critical", 0)
            st.write(
                f"**Queries ready for approval:** {n_queries} total "
                f"({n_critical} critical/major)"
            )
            risk_tier = (res.get("risk_score") or {}).get("risk_tier", "UNKNOWN")
            tmf_risk = (res.get("tmf_analysis") or {}).get("inspection_risk", "UNKNOWN")
            st.write(
                f"**Study risk tier:** {risk_tier} · "
                f"**TMF inspection risk:** {tmf_risk}"
            )
            if action == RecommendedAction.ESCALATE:
                st.error(
                    "⚠ ESCALATE: critical risk or inspection failure risk detected. "
                    "Notify CTM and Quality immediately."
                )
            if st.button("✅ Approve queries and confirm briefing"):
                st.success(
                    "ClinOps Lead sign-off recorded. In a live deployment the gateway "
                    "mints a scoped token and issues the approved EDC queries to sites "
                    "(audited high-risk write via edc.create_query)."
                )

# ── Tab 2: Issues & Queries ───────────────────────────────────────────────────
with tab_issues:
    res = st.session_state.ct_result
    if res:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Detected Operational Issues")
            issues = res.get("detected_issues", [])
            if issues:
                st.dataframe(issues, use_container_width=True)
            else:
                st.success("No operational issues detected.")

            st.subheader("Missing Data Flags")
            flags = res.get("missing_data_flags", [])
            if flags:
                st.dataframe(flags, use_container_width=True)
            else:
                st.success("No missing data flags.")

        with col2:
            st.subheader("Protocol Deviation Flags")
            devs = res.get("deviation_flags", [])
            if devs:
                st.dataframe(devs, use_container_width=True)
            else:
                st.success("No protocol deviation flags.")

            st.subheader("Drafted EDC Queries (Pending Approval)")
            qs = res.get("query_summary", {})
            if qs:
                st.json(qs)
            queries = res.get("data_queries", [])
            if queries:
                st.dataframe(
                    [{"id": q["draft_query_id"], "subject": q["subject_id"],
                      "site": q["site_id"], "severity": q["severity"],
                      "status": q["status"]}
                     for q in queries],
                    use_container_width=True,
                )
                with st.expander("View first query text"):
                    st.write(queries[0]["query_text"])
            else:
                st.info("No queries drafted.")
    else:
        st.info("Run the workflow to see issues and queries.")

# ── Tab 3: TMF Analysis ───────────────────────────────────────────────────────
with tab_tmf:
    res = st.session_state.ct_result
    if res:
        tmf = res.get("tmf_analysis", {})
        risk_color = {
            "LOW": "green", "MEDIUM": "orange",
            "HIGH": "red", "CRITICAL": "red",
        }.get(tmf.get("inspection_risk", ""), "gray")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completeness", f"{tmf.get('completeness_pct', 'N/A')}%")
        with col2:
            st.metric(
                "Inspection Ready",
                "✅ Yes" if tmf.get("inspection_ready") else "⚠ No",
            )
        with col3:
            st.markdown(
                f"**Inspection Risk:** :{risk_color}[{tmf.get('inspection_risk', 'N/A')}]"
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("Critical Gaps", len(tmf.get("critical_gaps", [])))
        with col5:
            st.metric("Major Gaps", len(tmf.get("major_gaps", [])))
        with col6:
            st.metric("Minor Gaps", len(tmf.get("minor_gaps", [])))

        if tmf.get("critical_gaps"):
            st.error("Critical TMF gaps (inspection failure risk):")
            for gap in tmf["critical_gaps"]:
                st.error(f"  • {gap}")
        if tmf.get("major_gaps"):
            st.warning("Major TMF gaps:")
            for gap in tmf["major_gaps"]:
                st.warning(f"  • {gap}")
        if tmf.get("findings"):
            st.subheader("TMF Findings")
            for finding in tmf["findings"]:
                st.write(f"• {finding}")
    else:
        st.info("Run the workflow to see TMF analysis.")

# ── Tab 4: Risk Score ─────────────────────────────────────────────────────────
with tab_risk:
    res = st.session_state.ct_result
    if res:
        rs = res.get("risk_score", {})
        tier = rs.get("risk_tier", "UNKNOWN")
        composite = rs.get("composite_score", 0)
        tier_color = {
            "LOW": "green", "MEDIUM": "orange",
            "HIGH": "red", "CRITICAL": "red",
        }.get(tier, "gray")

        st.markdown(f"## Risk Tier: :{tier_color}[{tier}]")
        st.progress(min(composite / 100, 1.0), text=f"Composite score: {composite}/100")

        st.subheader("Risk Factors")
        for factor in rs.get("factors", []):
            st.write(f"• {factor}")

        if rs.get("recommendations"):
            st.subheader("Recommendations")
            for rec in rs["recommendations"]:
                st.info(rec)

        st.subheader("Component Scores")
        comp = rs.get("component_scores", {})
        if comp:
            st.bar_chart(comp)
    else:
        st.info("Run the workflow to see the risk score.")

# ── Tab 5: Audit Trail ────────────────────────────────────────────────────────
with tab_audit:
    res = st.session_state.ct_result
    if res and res.get("audit_trail"):
        st.subheader("Audit Trail (GCP / ICH E6(R2) / 21 CFR Part 11)")
        st.dataframe(res["audit_trail"], use_container_width=True)
    else:
        st.info("Run the workflow to populate the audit trail.")

st.caption(
    "Decision-support tool for qualified clinical operations professionals. "
    "All AI-drafted EDC queries require review and approval by a ClinOps Lead "
    "before issuance to sites. The AI never issues queries or creates deviations autonomously."
)
