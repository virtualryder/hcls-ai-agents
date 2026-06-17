"""
Pharmacovigilance ICSR Intake Agent — Streamlit demo dashboard.

Showcases the full workflow: intake -> validity -> extract -> code_terms ->
duplicate_search -> seriousness_assessment -> narrative_draft -> quality_check ->
human_review_gate -> finalize. Runs with no API key in EXTRACT_MODE=demo.

The HITL sign-off is explicit: nothing is "submitted" until a PV Medical
Reviewer approves in the UI.
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

from agent.graph import build_pharmacovigilance_graph
from agent.state import RecommendedAction

st.set_page_config(
    page_title="Pharmacovigilance ICSR Intake Agent",
    page_icon="🛡️",
    layout="wide",
)

ROLES = ["PV_PROCESSOR", "PV_MEDICAL_REVIEWER"]


def load_cases():
    f = HERE / "data" / "fixtures" / "sample_cases.json"
    return json.loads(f.read_text())["cases"]


# ── Sidebar: identity + config ────────────────────────────────────────────────
st.sidebar.title("🛡️ Pharmacovigilance ICSR Intake")
st.sidebar.caption("AI-assisted ICSR processing — PV Medical Reviewer approves every submission.")
role = st.sidebar.selectbox("Acting role (from your IdP)", ROLES, index=0)
user_sub = st.sidebar.text_input("User ID", value="demo.pv.user")
os.environ.setdefault("EXTRACT_MODE", "demo")
st.sidebar.info(
    f"Mode: **{os.getenv('EXTRACT_MODE', 'demo')}** · "
    f"Connectors: **{os.getenv('CONNECTOR_MODE', 'fixture')}**"
)

cases = load_cases()
labels = [
    f"{c['case_id']} — {c['source_type']} ({c.get('context', {}).get('expected_outcome', 'unknown')})"
    for c in cases
]
choice = st.sidebar.selectbox("AE source record", range(len(cases)), format_func=lambda i: labels[i])
case = cases[choice]

st.title("ICSR Case Intake & Narrative Drafting")
st.write(
    f"**Case:** {case['case_id']} · **Source:** {case['source_type']} · "
    f"**Reporter:** {case.get('context', {}).get('reporter_name', 'unknown')} · "
    f"**Country:** {case.get('context', {}).get('reporter_country', 'unknown')}"
)

tab_run, tab_coding, tab_seriousness, tab_grounding, tab_audit = st.tabs(
    ["Narrative & Review", "Coding", "Seriousness", "Grounding & Quality", "Audit Trail"]
)

if "pv_result" not in st.session_state:
    st.session_state.pv_result = None

with tab_run:
    if st.button("▶ Run ICSR intake workflow", type="primary"):
        seed = {
            "case_id": case["case_id"],
            "source_type": case["source_type"],
            "raw_source": case["raw_source"],
            "acting_user_claims": {"sub": user_sub, "custom:hcls_role": role},
        }
        graph = build_pharmacovigilance_graph(use_memory=False)
        with st.spinner("Processing adverse event source…"):
            st.session_state.pv_result = graph.invoke(seed)

    res = st.session_state.pv_result
    if res:
        action = res.get("recommended_action")
        color = {
            RecommendedAction.APPROVE_DRAFT: "green",
            RecommendedAction.REVISE: "orange",
            RecommendedAction.ESCALATE: "red",
        }.get(action, "gray")
        st.markdown(
            f"**Disposition:** :{color}[{getattr(action, 'value', action)}] · "
            f"drafted by `{res.get('narrative_drafted_by')}` · "
            f"status `{res.get('case_status')}`"
        )

        # ICSR validity
        valid = res.get("is_valid_icsr", False)
        st.metric("ICSR Validity (4 elements)", "✅ Valid" if valid else "⚠ Invalid")
        if res.get("validity_notes"):
            for n in res["validity_notes"]:
                st.warning(n)

        st.subheader("Drafted ICSR Narrative (CIOMS/E2B-style)")
        st.write(res.get("narrative_text", ""))

        col1, col2 = st.columns(2)
        with col1:
            g = res.get("grounding_report", {})
            st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review")
            phi_ok = res.get("phi_check_passed", True)
            st.metric("PHI check", "✅ passed" if phi_ok else "🚨 FAILED — ESCALATE")
        with col2:
            elem_ok = res.get("required_elements_present", True)
            st.metric("Required elements", "✅ present" if elem_ok else "⚠ missing")
            qf = res.get("quality_findings", [])
            st.metric("Quality findings", len(qf))
            for f in qf:
                st.error(f)

        st.divider()
        st.subheader("👤 Human Review Gate (PV Medical Reviewer)")
        if role != "PV_MEDICAL_REVIEWER":
            st.info(
                "Switch acting role to PV_MEDICAL_REVIEWER to confirm causality, "
                "seriousness, and authorize case submission."
            )
        else:
            st.checkbox(
                "I have reviewed the narrative, coding, seriousness classification, "
                "grounding report, and quality findings."
            )
            st.write(f"Causality proposed: **{res.get('causality_assessment', 'UNKNOWN')}**")
            st.write(
                f"Seriousness: **{'SERIOUS' if res.get('is_serious') else 'NON-SERIOUS'}** "
                f"({', '.join(res.get('seriousness_criteria', []))})"
            )
            if res.get("reporting_clock_days"):
                st.warning(
                    f"Expedited reporting clock: **{res['reporting_clock_days']}-day**. "
                    f"Deadline: {res.get('reporting_deadline', 'TBD')}"
                )
            if st.button("✅ Confirm & submit ICSR to safety database"):
                st.success(
                    "Reviewer sign-off recorded with your verified identity. In a live "
                    "deployment the gateway mints a scoped token and submits the ICSR "
                    "to Argus/Veeva Safety (audited, high-risk write)."
                )

with tab_coding:
    res = st.session_state.pv_result
    if res:
        st.subheader("MedDRA Coding")
        st.json({
            "Preferred Term (PT)": res.get("meddra_pt"),
            "PT Code": res.get("meddra_pt_code"),
            "System Organ Class (SOC)": res.get("meddra_soc"),
        })
        st.subheader("WHODrug Coding")
        st.json({
            "WHODrug Preferred Name": res.get("whodrug_name"),
            "ATC Code": res.get("whodrug_atc"),
        })
        st.subheader("Extracted E2B(R3) Fields")
        e2b_fields = {
            "Patient age": res.get("patient_age"),
            "Patient sex": res.get("patient_sex"),
            "Reporter": res.get("reporter_name"),
            "Reporter type": res.get("reporter_type"),
            "Reporter country": res.get("reporter_country"),
            "Suspect drug": res.get("suspect_drug"),
            "Dose": res.get("suspect_dose"),
            "Route": res.get("suspect_route"),
            "Indication": res.get("suspect_indication"),
            "Event": res.get("event_description"),
            "Onset date": res.get("event_onset_date"),
            "Time to onset (days)": res.get("time_to_onset_days"),
            "Outcome": res.get("event_outcome"),
            "Dechallenge": res.get("dechallenge"),
            "Rechallenge": res.get("rechallenge"),
        }
        st.json(e2b_fields)
        if res.get("is_duplicate"):
            st.warning(
                f"⚠ Potential duplicate detected: "
                f"{len(res.get('duplicate_candidates', []))} candidate(s)"
            )
            st.json(res.get("duplicate_candidates"))
    else:
        st.info("Run the workflow to see coding results.")

with tab_seriousness:
    res = st.session_state.pv_result
    if res:
        is_serious = res.get("is_serious", False)
        st.metric(
            "Seriousness",
            "🔴 SERIOUS" if is_serious else "🟢 NON-SERIOUS",
        )
        criteria = res.get("seriousness_criteria", [])
        if criteria:
            st.write("**Criteria met:**")
            for c in criteria:
                st.markdown(f"- {c.replace('_', ' ').title()}")
        st.metric(
            "Expectedness",
            res.get("expectedness", "UNKNOWN"),
        )
        st.metric(
            "Causality (provisional — reviewer confirms)",
            res.get("causality_assessment", "UNKNOWN"),
        )
        clock = res.get("reporting_clock_days")
        if clock:
            st.metric("Reporting clock", f"{clock}-day expedited")
            deadline = res.get("reporting_deadline")
            if deadline:
                st.metric("Reporting deadline", deadline)
        else:
            st.metric("Reporting clock", "Not applicable (non-serious)")
    else:
        st.info("Run the workflow to see seriousness assessment.")

with tab_grounding:
    res = st.session_state.pv_result
    if res:
        g = res.get("grounding_report", {})
        st.subheader("Grounding Report")
        st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review")
        if not g.get("grounded"):
            st.warning(
                f"Ungrounded numbers: {g.get('ungrounded_numbers')}\n\n"
                f"Ungrounded entities: {g.get('ungrounded_entities')}"
            )
        st.json(g)

        st.subheader("PHI Check")
        phi_ok = res.get("phi_check_passed", True)
        if phi_ok:
            st.success("PHI check passed — no raw PII detected in narrative.")
        else:
            st.error("PHI check FAILED — ESCALATE immediately.")

        st.subheader("Required Element Check")
        elem_ok = res.get("required_elements_present", True)
        if elem_ok:
            st.success("All required ICSR narrative elements present.")
        else:
            st.warning("One or more required elements missing.")
            for f in res.get("quality_findings", []):
                st.error(f)
    else:
        st.info("Run the workflow to see grounding and quality results.")

with tab_audit:
    res = st.session_state.pv_result
    if res and res.get("audit_trail"):
        st.subheader("Audit Trail (21 CFR Part 11 / GVP Module VI)")
        st.dataframe(res["audit_trail"], use_container_width=True)
    else:
        st.info("Run the workflow to populate the audit trail.")

st.caption(
    "Decision-support tool for qualified PV professionals. All AI output requires "
    "review and confirmation by a PV Medical Reviewer before ICSR submission. "
    "The AI never submits to a regulatory authority autonomously."
)
