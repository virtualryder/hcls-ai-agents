"""
RWE/HEOR Agent — Streamlit demo dashboard.

Full multi-tab workflow: intake research question, define cohort, run de-identified
RWD query, assess data quality, synthesize evidence with grounding checks, and
present to an Epidemiologist for approval. All statistics pre-computed by the
validated compute pipeline; LLM synthesizes narrative only.
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

from agent.graph import build_rwe_heor_graph
from agent.state import RecommendedAction

st.set_page_config(
    page_title="RWE/HEOR Evidence Agent",
    page_icon="📊",
    layout="wide",
)

ROLES = ["EPIDEMIOLOGIST", "HEOR_ANALYST"]


def load_requests():
    f = HERE / "data" / "fixtures" / "sample_rwe_requests.json"
    return json.loads(f.read_text())["requests"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📊 RWE/HEOR Evidence Agent")
st.sidebar.caption(
    "AI evidence synthesis — Epidemiologist reviews all findings. "
    "LLM synthesizes narrative only; statistics are pre-computed."
)
role = st.sidebar.selectbox("Acting role (from your IdP)", ROLES, index=0)
user_sub = st.sidebar.text_input("User ID", value="demo.epidemiologist")
os.environ.setdefault("EXTRACT_MODE", "demo")
st.sidebar.info(
    f"Mode: **{os.getenv('EXTRACT_MODE', 'demo')}** · "
    f"Connectors: **{os.getenv('CONNECTOR_MODE', 'fixture')}**"
)
st.sidebar.caption(
    "PHI note: all data is aggregate de-identified (>= 11 per cell). "
    "PHI never crosses the query boundary."
)

reqs = load_requests()
labels = [
    f"{r['request_id']} — {r['indication']} ({r['study_design_type']})"
    for r in reqs
]
choice = st.sidebar.selectbox(
    "Research question", range(len(reqs)), format_func=lambda i: labels[i]
)
req = reqs[choice]

st.title("Real-World Evidence & Health Economics Analysis")
st.write(
    f"**{req['indication']}** · {req['intervention']} vs {req['comparator']} "
    f"· {req['time_horizon']} · {req['data_source']}"
)
st.caption(req.get("research_question", ""))

(tab_run, tab_cohort, tab_quality, tab_grounding, tab_audit) = st.tabs([
    "Evidence Synthesis & Review",
    "Cohort & Statistics",
    "Data Quality",
    "Grounding Report",
    "Audit Trail",
])

if "rwe_result" not in st.session_state:
    st.session_state.rwe_result = None

with tab_run:
    if st.button("▶ Run RWE synthesis workflow", type="primary"):
        seed = {
            k: req[k]
            for k in (
                "request_id", "research_question", "study_design_type",
                "indication", "intervention", "comparator", "outcome",
                "time_horizon", "data_source", "instructions",
            )
        }
        seed["acting_user_claims"] = {"sub": user_sub, "custom:hcls_role": role}
        graph = build_rwe_heor_graph(use_memory=False)
        with st.spinner("Running cohort query and synthesizing evidence…"):
            st.session_state.rwe_result = graph.invoke(seed)

    res = st.session_state.rwe_result
    if res:
        action = res.get("recommended_action")
        color = {
            RecommendedAction.APPROVE_SYNTHESIS: "green",
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
                "ESCALATED: causal language or cell-suppression issue detected. "
                "Do not publish or submit until resolved."
            )

        g = res.get("grounding_report", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review")
        with col2:
            qa = res.get("data_quality", {})
            st.metric("Data quality score", f"{qa.get('quality_score', 'N/A')}/100")
        with col3:
            st.metric(
                "Quality findings", len(res.get("quality_findings", []))
            )

        st.subheader("Evidence Synthesis")
        st.write(res.get("evidence_synthesis", ""))

        if res.get("quality_findings"):
            for f in res["quality_findings"]:
                st.warning(f)

        st.divider()
        st.subheader("👤 Human Review Gate (Epidemiologist)")
        if role != "EPIDEMIOLOGIST":
            st.info(
                "Switch acting role to EPIDEMIOLOGIST to review and approve "
                "the synthesis for use in publications or regulatory submissions."
            )
        else:
            st.checkbox(
                "I have reviewed the evidence synthesis, grounding report, "
                "data quality findings, and limitations."
            )
            if st.button("✅ Approve synthesis for publication/regulatory use"):
                st.success(
                    "Epidemiologist approval recorded. In a live deployment the synthesis "
                    "is locked, audit trail is sealed, and the record is submitted to "
                    "the publication management system."
                )
    else:
        st.info("Select a research question and click 'Run RWE synthesis workflow'.")

with tab_cohort:
    res = st.session_state.rwe_result
    if res:
        st.subheader("Cohort Definition (Computable Spec)")
        cd = res.get("cohort_definition", {})
        if not res.get("cohort_definition_valid", True):
            for issue in res.get("cohort_definition_issues", []):
                st.warning(f"Cohort definition issue: {issue}")
        st.json(cd)

        st.subheader("Cohort Results (De-identified, Aggregate)")
        st.json(res.get("cohort_results", {}))

        st.subheader("Summary Statistics (Validated Compute)")
        st.json(res.get("summary_statistics", {}))
        st.caption(
            "Statistics are computed by a validated pipeline. "
            "The LLM synthesizes narrative only and does not generate estimates."
        )
    else:
        st.info("Run the workflow to see cohort data.")

with tab_quality:
    res = st.session_state.rwe_result
    if res:
        qa = res.get("data_quality", {})
        st.subheader("Data Quality Assessment")
        score = qa.get("quality_score", 0)
        color = "green" if score >= 80 else ("orange" if score >= 60 else "red")
        st.markdown(f"**Quality score:** :{color}[{score}/100]")
        st.metric("Cohort balance", qa.get("cohort_balance", "N/A"))
        st.metric("Data completeness", f"{qa.get('data_completeness_pct', 'N/A')}%")
        st.metric(
            "Cell suppression required",
            "Yes" if qa.get("cell_suppression_required") else "No",
        )
        if qa.get("concerns"):
            st.subheader("Concerns")
            for c in qa["concerns"]:
                st.error(c)
        if qa.get("warnings"):
            st.subheader("Warnings")
            for w in qa["warnings"]:
                st.warning(w)
        if qa.get("confounding_flags"):
            st.subheader("Confounding Flags")
            for f in qa["confounding_flags"]:
                st.info(f)
    else:
        st.info("Run the workflow to see data quality results.")

with tab_grounding:
    res = st.session_state.rwe_result
    if res:
        g = res.get("grounding_report", {})
        st.subheader("Grounding Report")
        st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review required")
        if not g.get("grounded"):
            st.warning(
                f"Ungrounded numbers: {g.get('ungrounded_numbers')}\n\n"
                f"Ungrounded entities: {g.get('ungrounded_entities')}"
            )
        st.json(g)

        st.subheader("Quality Findings")
        findings = res.get("quality_findings", [])
        if not findings:
            st.success("No quality issues found.")
        else:
            for f in findings:
                st.error(f)
    else:
        st.info("Run the workflow to see grounding results.")

with tab_audit:
    res = st.session_state.rwe_result
    if res and res.get("audit_trail"):
        st.subheader("Audit Trail")
        st.dataframe(res["audit_trail"], use_container_width=True)
    else:
        st.info("Run the workflow to populate the audit trail.")

st.caption(
    "Decision-support tool for qualified epidemiologists. "
    "All AI output requires review by an Epidemiologist before use in publications or submissions. "
    "RWE establishes association, not causation. PHI stays at source."
)
