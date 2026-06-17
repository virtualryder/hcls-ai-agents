# app.py -- Quality CAPA Agent Streamlit dashboard
from __future__ import annotations
import os, sys
from pathlib import Path
import streamlit as st
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from agent.graph import build_quality_capa_graph
from agent.state import RecommendedAction

ROLES = ["QA_SPECIALIST", "QUALIFIED_PERSON"]
DEMO_COMPLAINTS = [
    "COMP-2026-001 -- Major: particulate matter in vial (Lot LOT-2026-001)",
    "COMP-2026-002 -- Minor: temperature excursion during storage (Lot LOT-2026-002)",
    "COMP-2026-003 -- Critical: sterility out-of-spec, regulatory reporting (Lot LOT-2026-003)",
]
_FIXTURE_MAP = {
    "COMP-2026-001": {"complaint_id": "COMP-2026-001", "product": "Sterile Injectable Alpha", "lot_number": "LOT-2026-001", "site": "SITE-MFG-01", "event_type": "PRODUCT_DEFECT", "severity": "MAJOR", "description": "Visible particulate matter observed in 3 vials from lot LOT-2026-001 of Sterile Injectable Alpha at SITE-MFG-01."},
    "COMP-2026-002": {"complaint_id": "COMP-2026-002", "product": "Biologic Formulation Beta", "lot_number": "LOT-2026-002", "site": "SITE-MFG-02", "event_type": "TEMPERATURE_EXCURSION", "severity": "MINOR", "description": "Temperature excursion for lot LOT-2026-002. Data logger indicated 12 hours at 9 degrees C instead of required 2-8 degrees C."},
    "COMP-2026-003": {"complaint_id": "COMP-2026-003", "product": "Sterile Ophthalmic Gamma", "lot_number": "LOT-2026-003", "site": "SITE-MFG-01", "event_type": "STERILITY_FAILURE", "severity": "CRITICAL", "description": "Sterility test out-of-specification for lot LOT-2026-003. Microbial growth in 2 of 10 units. Regulatory reporting under 21 CFR 314.81."},
}

def _claims(role):
    return {"sub": f"demo-{role.lower()}", "custom:hcls_role": role, "custom:site": "SITE-MFG-01"}

def run_workflow(complaint_key, role):
    fixture = _FIXTURE_MAP[complaint_key]
    initial = {**fixture, "acting_user_claims": _claims(role), "audit_trail": [], "completed_steps": [], "errors": [], "revision_count": 0}
    graph = build_quality_capa_graph(use_memory=False)
    result = None
    for event in graph.stream(initial, stream_mode="values"):
        result = event
    return result

def main():
    st.set_page_config(page_title="Quality CAPA Agent", layout="wide")
    st.title("Quality CAPA Agent")
    st.caption("21 CFR Part 820 / ICH Q10 -- AI-assisted CAPA planning with HITL gate")
    with st.sidebar:
        st.header("Configuration")
        role = st.selectbox("Your Role", ROLES, index=0)
        complaint_label = st.selectbox("Select Complaint", DEMO_COMPLAINTS, index=0)
        complaint_key = complaint_label.split(" ")[0]
        if st.button("Run CAPA Workflow", type="primary"):
            with st.spinner("Running..."):
                try:
                    st.session_state["result"] = run_workflow(complaint_key, role)
                    st.session_state["role"] = role
                    st.success("Complete")
                except Exception as exc:
                    st.error(f"Error: {exc}")
        st.caption(f"Role: **{role}**")
    result = st.session_state.get("result")
    if not result:
        st.info("Select a complaint and run the workflow.")
        return
    active_role = st.session_state.get("role", role)
    t1, t2, t3, t4, t5 = st.tabs(["CAPA Plan & Review","Classification","Root Cause Analysis","Grounding & Quality","Audit Trail"])
    with t1:
        st.subheader("CAPA Plan")
        if result.get("capa_plan"):
            st.markdown(result["capa_plan"])
        action = result.get("recommended_action")
        if action:
            v = action.value if hasattr(action,"value") else str(action)
            col = {"APPROVE_CAPA":"green","REVISE":"orange","ESCALATE":"red"}.get(v,"gray")
            st.markdown(f"**Action:** :{col}[{v}]")
        st.markdown(f"**Status:** `{result.get('case_status','?')}`")
        if active_role == "QUALIFIED_PERSON":
            st.markdown("---")
            st.subheader("QP Approval Gate")
            dec = st.radio("Decision", ["Approve", "Reject"], horizontal=True)
            notes = st.text_area("Notes", height=60)
            if st.button("Submit", type="primary"):
                st.session_state["qp"] = {"approved": dec=="Approve", "notes": notes}
                st.success("Recorded.") if dec=="Approve" else st.warning("Rejected.")
            if st.session_state.get("qp"):
                st.json(st.session_state["qp"])
        else:
            st.info("HITL gate restricted to QUALIFIED_PERSON.")
    with t2:
        st.subheader("Classification")
        cls = result.get("classification", {})
        if cls:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Event Type", cls.get("event_type","--"))
                st.metric("Severity", cls.get("severity","--"))
                st.metric("Risk Level", cls.get("risk_level","--"))
            with c2:
                st.metric("Reg Reporting", "YES" if cls.get("regulatory_reporting_required") else "NO")
                st.metric("Recurrence Risk", cls.get("recurrence_risk","--"))
                st.metric("Investigation", cls.get("investigation_method","--"))
            if cls.get("ishikawa_categories"):
                st.write("Ishikawa: " + ", ".join(cls["ishikawa_categories"]))
        if result.get("complaint_record"):
            with st.expander("Complaint Record"):
                st.json(result["complaint_record"])
    with t3:
        st.subheader("Root Cause Analysis")
        for i, h in enumerate(result.get("root_cause_hypotheses",[]), 1):
            st.markdown(f"**{i}. {h.get('category','').upper()}** ({h.get('confidence',0):.0%}): {h.get('hypothesis','')}")
        similar = result.get("similar_events",[])
        if similar:
            with st.expander(f"Similar Events ({len(similar)})"):
                for ev in similar:
                    s = ev.get("score", ev.get("similarity_score",0))
                    st.markdown(f"- **{ev.get('id') or ev.get('complaint_id','?')}** ({s:.2f}): {ev.get('description','')[:100]}")
        clusters = result.get("clusters",[])
        if clusters:
            with st.expander(f"Clusters ({len(clusters)})"):
                for c in clusters:
                    st.markdown(f"- **{c.get('cluster_id')}** {c.get('theme')} ({c.get('count')} events)")
    with t4:
        st.subheader("Grounding & Quality")
        findings = result.get("quality_findings",[])
        if findings:
            st.error(f"{len(findings)} finding(s):")
            for f in findings: st.markdown(f"- {f}")
        else:
            st.success("No findings.")
        g = result.get("grounding_report",{})
        if g:
            if g.get("grounded", True):
                st.success("Grounding: PASS")
            else:
                st.warning(f"Grounding: FAIL -- ungrounded nums: {g.get('ungrounded_numbers',[])}; entities: {g.get('ungrounded_entities','')}")
        if result.get("drafted_by"): st.caption(f"Drafted by: {result['drafted_by']}")
    with t5:
        st.subheader("Audit Trail")
        for e in result.get("audit_trail",[]):
            ts = e.get("timestamp","")[:19].replace("T"," ")
            hitl = " [HITL]" if e.get("human_review_required") else ""
            st.markdown(f"`{ts}` **{e.get('node','?')}**{hitl} -- {e.get('action','')} *(actor: {e.get('actor','')})*")
        steps = result.get("completed_steps",[])
        if steps: st.markdown("Steps: " + " -> ".join(steps))

if __name__ == "__main__":
    main()
