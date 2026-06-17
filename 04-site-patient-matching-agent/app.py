# app.py — Site Patient Matching Agent: multi-tab Streamlit dashboard
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR.parent / "platform_core"))
os.environ.setdefault("EXTRACT_MODE", "demo")

import streamlit as st

from agent.graph import build_site_patient_matching_graph
from agent.state import RecommendedAction

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Site & Patient Matching Agent",
    page_icon="🏥",
    layout="wide",
)

# ── Sidebar: role + fixture selector ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## Site & Patient Matching")
    st.markdown("*Agent 04 — Clinical Trial Feasibility*")
    st.divider()

    role = st.selectbox(
        "User Role",
        ["EPIDEMIOLOGIST", "SITE_SELECTION_LEAD", "CTM"],
        help="Controls what actions are visible (e.g. approval button).",
    )
    st.caption(f"Acting as: **{role}**")
    st.divider()

    FIXTURES_PATH = AGENT_DIR / "data" / "fixtures" / "sample_matching_requests.json"
    try:
        with open(FIXTURES_PATH) as fh:
            _requests = json.load(fh).get("requests", [])
        request_labels = [
            f"{r['request_id']} — {r.get('indication', 'N/A')}" for r in _requests
        ]
    except Exception:
        _requests = []
        request_labels = []

    selected_label = st.selectbox("Sample Matching Request", request_labels or ["(no fixtures)"])
    selected_request = {}
    if _requests and selected_label:
        idx = request_labels.index(selected_label)
        selected_request = _requests[idx]

    st.divider()
    run_btn = st.button("Run Matching Workflow", type="primary", use_container_width=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "graph" not in st.session_state:
    st.session_state.graph = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "hitl_pending" not in st.session_state:
    st.session_state.hitl_pending = False
if "errors" not in st.session_state:
    st.session_state.errors = []

# ── Run workflow ──────────────────────────────────────────────────────────────
if run_btn and selected_request:
    with st.spinner("Running site & patient matching workflow…"):
        try:
            import uuid
            thread_id = f"spm-{uuid.uuid4().hex[:8]}"
            state_input = {**selected_request,
                           "acting_user_claims": {"sub": f"demo@example.com",
                                                  "custom:hcls_role": role}}
            g = build_site_patient_matching_graph(use_memory=True)
            config = {"configurable": {"thread_id": thread_id}}
            result = g.invoke(state_input, config=config)
            snapshot = g.get_state(config)
            hitl_pending = bool(snapshot.next)

            st.session_state.graph = g
            st.session_state.thread_id = thread_id
            st.session_state.result = result
            st.session_state.hitl_pending = hitl_pending
            st.session_state.errors = []
        except Exception as exc:
            st.session_state.errors = [str(exc)]

# ── Helper to re-read latest state ───────────────────────────────────────────
def _latest():
    if st.session_state.graph and st.session_state.thread_id:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        snap = st.session_state.graph.get_state(config)
        return snap.values
    return st.session_state.result or {}

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("Site & Patient Matching Agent")
st.caption(
    "Translates eligibility criteria to computable cohort logic, "
    "ranks sites by eligible patient pool (de-identified RWD), "
    "checks demographic representativeness, and routes to human approval."
)

if st.session_state.errors:
    for e in st.session_state.errors:
        st.error(f"Workflow error: {e}")

state = _latest()

TAB_RANKING, TAB_COHORT, TAB_EQUITY, TAB_ELIGIBILITY, TAB_AUDIT = st.tabs([
    "Ranking & Review",
    "Cohort Estimates",
    "Equity & Fairness",
    "Eligibility Query",
    "Audit Trail",
])

# ── Tab 1: Ranking & Review ───────────────────────────────────────────────────
with TAB_RANKING:
    if not state:
        st.info("Select a matching request from the sidebar and click **Run Matching Workflow**.")
    else:
        action = state.get("recommended_action", "")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            total_elig = state.get("cohort_results", {}).get("total_eligible", "—")
            st.metric("Total Eligible Patients", total_elig)
        with c2:
            n_sites = len(state.get("site_rankings", []))
            st.metric("Sites Ranked", n_sites)
        with c3:
            n_flags = len(state.get("fairness_flags", []))
            st.metric("Fairness Flags", n_flags)
        with c4:
            action_label = action.value if hasattr(action, "value") else str(action)
            color = {"APPROVE_RANKING": "green", "REVISE": "orange",
                     "ESCALATE": "red"}.get(action_label, "gray")
            st.markdown(
                f"**Disposition:** :{color}[{action_label}]",
                help="Set by fairness_review node.",
            )

        st.divider()
        report = state.get("ranking_report", "")
        if report:
            st.subheader("Site Feasibility & Ranking Report")
            st.markdown(report)

        qf = state.get("quality_findings", [])
        gr = state.get("grounding_report", {})
        if qf or not gr.get("grounded", True):
            with st.expander("Quality & Grounding Issues", expanded=True):
                if qf:
                    for f in qf:
                        st.warning(f)
                ungrounded = gr.get("ungrounded_numbers", []) + gr.get("ungrounded_entities", [])
                for u in ungrounded:
                    st.error(f"Ungrounded: {u}")

        # HITL approval — visible to SITE_SELECTION_LEAD and CTM only
        if st.session_state.hitl_pending:
            if role in ("SITE_SELECTION_LEAD", "CTM"):
                st.divider()
                st.subheader("Human Review Gate")
                st.warning(
                    "This site ranking requires approval by the Site Selection Lead "
                    "before any site outreach is initiated."
                )
                col_a, col_r, col_e = st.columns(3)
                approved = col_a.button("Approve Ranking", type="primary")
                revise = col_r.button("Return for Revision")
                escalate = col_e.button("Escalate to CTM")

                decision = None
                if approved:
                    decision = "APPROVE_RANKING"
                elif revise:
                    decision = "REVISE"
                elif escalate:
                    decision = "ESCALATE"

                if decision:
                    g = st.session_state.graph
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    g.update_state(config, {"case_status": "APPROVED"})
                    final = g.invoke(None, config=config)
                    st.session_state.result = final
                    st.session_state.hitl_pending = False
                    st.success(f"Decision recorded: {decision}. Workflow finalized.")
                    st.rerun()
            else:
                st.info(
                    f"Pending HITL approval by Site Selection Lead. "
                    f"Current role ({role}) cannot approve."
                )

# ── Tab 2: Cohort Estimates ───────────────────────────────────────────────────
with TAB_COHORT:
    if not state:
        st.info("Run the workflow to see cohort feasibility estimates.")
    else:
        est = state.get("cohort_estimates", {})
        if not est:
            st.info("Cohort estimates not yet computed.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Projected Enrollees", est.get("total_projected_enrollees", "—"))
            with c2:
                st.metric("Target Enrollment", est.get("target_enrollment", "—"))
            with c3:
                feasible = est.get("portfolio_feasible", False)
                st.metric("Portfolio Feasible", "Yes" if feasible else "No")

            shortfall = est.get("shortfall", 0)
            if shortfall > 0:
                st.warning(f"Enrollment shortfall: {shortfall} subjects. Consider adding sites.")

            months = est.get("months_to_target")
            if months:
                st.info(
                    f"Estimated months to reach enrollment target across portfolio: **{months}**"
                )

            st.subheader("Site-Level Feasibility Estimates")
            sites_data = est.get("sites", [])
            if sites_data:
                import pandas as pd
                df = pd.DataFrame([{
                    "Site": s["site_id"],
                    "Eligible": s["eligible_count"],
                    "Projected Enrollees": s["projected_enrollees"],
                    "Months to Target": s.get("months_to_target", "N/A"),
                    "Feasible": "Yes" if s["feasible"] else "No",
                    "Recommendation": s["recommendation"],
                } for s in sites_data])
                st.dataframe(df, use_container_width=True)

            top = est.get("top_recommended_sites", [])
            if top:
                st.success(f"Top recommended sites for activation: {', '.join(top)}")

# ── Tab 3: Equity & Fairness ──────────────────────────────────────────────────
with TAB_EQUITY:
    if not state:
        st.info("Run the workflow to see equity analysis.")
    else:
        flags = state.get("fairness_flags", [])
        rankings = state.get("site_rankings", [])

        st.subheader("Demographic Representativeness Analysis")
        st.caption(
            "Sites are evaluated against US disease prevalence benchmarks for "
            "demographic representation. Flags are advisory — a SITE_SELECTION_LEAD "
            "must review before outreach."
        )

        if flags:
            for flag in flags:
                sev = flag.get("severity", "MODERATE")
                desc = flag.get("description", str(flag))
                if sev == "CRITICAL":
                    st.error(f"CRITICAL | {desc}")
                elif sev == "MODERATE":
                    st.warning(f"MODERATE | {desc}")
                else:
                    st.info(desc)
        else:
            st.success("No demographic under-representation flags identified.")

        if rankings:
            st.divider()
            st.subheader("Site Demographics Breakdown")
            rows = []
            for site in rankings:
                demo = site.get("demographics", {})
                rows.append({
                    "Rank": site.get("rank", "—"),
                    "Site": site.get("site_id", "—"),
                    "Region": site.get("region", "—"),
                    "Eligible": site.get("eligible_count", 0),
                    "% Female": demo.get("pct_female", "—"),
                    "% Hispanic": demo.get("pct_hispanic", "—"),
                    "% Black": demo.get("pct_black", "—"),
                })
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ── Tab 4: Eligibility Query ──────────────────────────────────────────────────
with TAB_ELIGIBILITY:
    if not state:
        st.info("Run the workflow to see the translated eligibility query.")
    else:
        cq = state.get("cohort_query", {})
        if not cq:
            st.info("Cohort query not yet computed.")
        else:
            st.subheader("Translated Computable Cohort Query")
            st.caption(
                f"Indication: **{cq.get('indication', '—')}** | "
                f"CDISC-compliant: **{cq.get('cdisc_compliant', False)}** | "
                f"Translated fields: **{cq.get('translated_fields', 0)}**"
            )
            notes = cq.get("translation_notes", [])
            for n in notes:
                st.info(n)

            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader("Inclusion Filters")
                filters = cq.get("filters", [])
                labs = cq.get("labs", [])
                if filters:
                    for f in filters:
                        st.code(
                            f"{f.get('field')} {f.get('op')} {f.get('value')} "
                            f"[{f.get('cdisc_domain', '')}]"
                        )
                if labs:
                    for lab in labs:
                        st.code(
                            f"{lab.get('test_name')} {lab.get('op')} {lab.get('value')} "
                            f"[{lab.get('cdisc_domain', 'LB')}]"
                        )
                if not filters and not labs:
                    st.caption("No inclusion filters.")

            with col_r:
                st.subheader("Exclusion Filters")
                excl = cq.get("exclusion_filters", [])
                if excl:
                    for e in excl:
                        if e.get("type") == "text_exclusion":
                            st.code(f"EXCLUDE: {e.get('description')}")
                        else:
                            st.code(
                                f"{e.get('field')} {e.get('op')} {e.get('value')} "
                                f"[{e.get('cdisc_domain', '')}]"
                            )
                else:
                    st.caption("No exclusion filters.")

            phi_note = state.get("cohort_results", {}).get("phi_note", "")
            if phi_note:
                st.divider()
                st.info(phi_note)

# ── Tab 5: Audit Trail ────────────────────────────────────────────────────────
with TAB_AUDIT:
    if not state:
        st.info("Run the workflow to see the audit trail.")
    else:
        trail = state.get("audit_trail", [])
        st.subheader(f"Audit Trail ({len(trail)} entries)")
        st.caption(
            "Every data access, AI action, and human decision is recorded "
            "per 21 CFR Part 11 / GCP audit requirements."
        )
        if trail:
            for i, entry in enumerate(trail):
                node = entry.get("node", "—")
                action = entry.get("action", "—")
                ts = entry.get("timestamp", "—")
                sources = entry.get("data_sources_accessed", [])
                hr = entry.get("human_review_required", False)
                with st.expander(f"{i+1}. [{node}] {action[:80]}", expanded=(i == len(trail) - 1)):
                    cols = st.columns(3)
                    cols[0].markdown(f"**Timestamp:** {ts}")
                    cols[1].markdown(f"**Actor:** {entry.get('actor', 'ai_agent')}")
                    cols[2].markdown(f"**Human Review:** {'Yes' if hr else 'No'}")
                    if sources:
                        st.markdown(f"**Data Sources:** {', '.join(sources)}")
                    model = entry.get("ai_model_used", "")
                    if model:
                        st.markdown(f"**Model:** {model}")

        errs = state.get("errors", [])
        if errs:
            st.divider()
            st.subheader("Recoverable Errors")
            for e in errs:
                st.warning(f"[{e.get('step', '?')}] {e.get('error', e)}")
