# app.py -- Protocol Design Agent Streamlit dashboard
from __future__ import annotations
import os, sys
from pathlib import Path
import streamlit as st
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from agent.graph import build_protocol_design_graph
from agent.state import RecommendedAction

ROLES = ["CLINICAL_SCIENTIST", "MEDICAL_REVIEWER"]
DEMO_REQUESTS = [
    "PROTO-2026-001 -- NSCLC Phase 2 RCT (PFS primary endpoint)",
    "PROTO-2026-002 -- T2DM Phase 3 RCT (HbA1c primary endpoint)",
    "PROTO-2026-003 -- Heart Failure Phase 3 RCT (composite endpoint)",
]
_FIXTURE_MAP = {
    "PROTO-2026-001": {"request_id":"PROTO-2026-001","indication":"non-small cell lung cancer","phase":"Phase 2","therapeutic_area":"Oncology","primary_objective":"evaluate progression-free survival with experimental PD-L1 inhibitor versus chemotherapy","target_population":"adults with locally advanced or metastatic NSCLC, ECOG PS 0-1","study_design":"Randomized Controlled Trial","instructions":"Draft endpoints (PFS primary, OS secondary), eligibility, and visit schedule."},
    "PROTO-2026-002": {"request_id":"PROTO-2026-002","indication":"type 2 diabetes mellitus","phase":"Phase 3","therapeutic_area":"Endocrinology","primary_objective":"demonstrate superiority of investigational GLP-1 agonist on HbA1c reduction","target_population":"adults aged 18-75 with type 2 diabetes mellitus, baseline HbA1c 7.5-10.5%","study_design":"Randomized Controlled Trial","instructions":"Draft primary and secondary endpoints, eligibility, and 52-week visit schedule."},
    "PROTO-2026-003": {"request_id":"PROTO-2026-003","indication":"heart failure with reduced ejection fraction","phase":"Phase 3","therapeutic_area":"Cardiovascular","primary_objective":"evaluate effect of novel SGLT2 inhibitor on composite cardiovascular endpoint","target_population":"adults with heart failure, NYHA Class II-III, LVEF less than 40%","study_design":"Randomized Controlled Trial","instructions":"Draft composite endpoint definition, eligibility, and 24-month visit schedule."},
}

def _claims(role):
    return {"sub": f"demo-{role.lower()}", "custom:hcls_role": role}

def run_workflow(req_key, role):
    fixture = _FIXTURE_MAP[req_key]
    initial = {**fixture, "acting_user_claims": _claims(role), "audit_trail": [], "completed_steps": [], "errors": [], "revision_count": 0}
    graph = build_protocol_design_graph(use_memory=False)
    result = None
    for event in graph.stream(initial, stream_mode="values"):
        result = event
    return result

def main():
    st.set_page_config(page_title="Protocol Design Agent", layout="wide")
    st.title("Protocol Design Agent")
    st.caption("ICH E6(R2) / 21 CFR Part 11 -- AI-assisted protocol authoring with HITL gate")
    with st.sidebar:
        st.header("Configuration")
        role = st.selectbox("Your Role", ROLES, index=0)
        req_label = st.selectbox("Select Protocol Request", DEMO_REQUESTS, index=0)
        req_key = req_label.split(" ")[0]
        if st.button("Run Protocol Workflow", type="primary"):
            with st.spinner("Running..."):
                try:
                    st.session_state["result"] = run_workflow(req_key, role)
                    st.session_state["role"] = role
                    st.success("Complete")
                except Exception as exc:
                    st.error(f"Error: {exc}")
        st.caption(f"Role: **{role}**")
    result = st.session_state.get("result")
    if not result:
        st.info("Select a request and run the workflow.")
        return
    active_role = st.session_state.get("role", role)
    t1, t2, t3, t4, t5, t6 = st.tabs(["Protocol Draft & Review","Regulatory Guidance","Feasibility","Risk Assessment","Grounding & Quality","Audit Trail"])
    with t1:
        st.subheader("Protocol Draft")
        draft = result.get("draft_protocol", "")
        if draft:
            st.markdown(draft)
        else:
            st.warning("No draft generated.")
        action = result.get("recommended_action")
        if action:
            v = action.value if hasattr(action,"value") else str(action)
            col = {"APPROVE_DRAFT":"green","REVISE":"orange","ESCALATE":"red"}.get(v,"gray")
            st.markdown(f"**Action:** :{col}[{v}]")
        st.markdown(f"**Status:** `{result.get('protocol_status','?')}`")
        if active_role == "MEDICAL_REVIEWER":
            st.markdown("---")
            st.subheader("Medical Reviewer Approval Gate")
            dec = st.radio("Decision", ["Approve","Reject"], horizontal=True)
            notes = st.text_area("Notes", height=60)
            if st.button("Submit", type="primary"):
                st.session_state["mr"] = {"approved": dec=="Approve","notes": notes}
                st.success("Recorded.") if dec=="Approve" else st.warning("Rejected.")
            if st.session_state.get("mr"): st.json(st.session_state["mr"])
        else:
            st.info("HITL gate restricted to MEDICAL_REVIEWER.")
    with t2:
        st.subheader("Regulatory Guidance")
        hits = result.get("guidance_hits", [])
        if hits:
            for h in hits:
                st.markdown(f"**{h.get('ref','')}** ({h.get('agency','')}) -- {h.get('title','')}")
        else:
            st.warning("No guidance found.")
    with t3:
        st.subheader("Feasibility")
        fa = result.get("feasibility_assessment", {})
        if fa:
            c1, c2 = st.columns(2)
            with c1:
                est = fa.get("cohort_estimate", {})
                st.metric("Total Eligible", est.get("total_eligible","--"))
                st.metric("Sites with Data", est.get("sites_with_data","--"))
            with c2:
                st.metric("Feasibility", fa.get("feasibility","--"))
                st.metric("Enrollment Target", fa.get("enrollment_target","--"))
            prec = fa.get("precedents", [])
            if prec:
                with st.expander(f"Precedent Studies ({len(prec)})"):
                    for p in prec:
                        st.markdown(f"- **{p.get('study_id','')}** {p.get('indication','')} {p.get('phase','')} -- {p.get('actual_enrolled','')} enrolled")
        else:
            st.warning("No feasibility data.")
    with t4:
        st.subheader("Risk Assessment")
        op_risks = result.get("operational_risks", [])
        reg_risks = result.get("regulatory_risks", [])
        if reg_risks:
            st.error(f"{len(reg_risks)} regulatory risk(s):")
            for r in reg_risks: st.markdown(f"- {r}")
        else:
            st.success("No regulatory risks flagged.")
        if op_risks:
            st.warning(f"{len(op_risks)} operational risk(s):")
            for r in op_risks: st.markdown(f"- {r}")
    with t5:
        st.subheader("Grounding & Quality")
        findings = result.get("quality_findings", [])
        if findings:
            st.error(f"{len(findings)} finding(s):")
            for f in findings: st.markdown(f"- {f}")
        else:
            st.success("No findings.")
        g = result.get("grounding_report", {})
        if g:
            if g.get("grounded", True):
                st.success("Grounding: PASS")
            else:
                st.warning(f"Grounding: FAIL -- ungrounded nums: {g.get('ungrounded_numbers',[])}; entities: {g.get('ungrounded_entities','')}")
        if result.get("drafted_by"): st.caption(f"Drafted by: {result['drafted_by']}")
    with t6:
        st.subheader("Audit Trail")
        for e in result.get("audit_trail",[]):
            ts = e.get("timestamp","")[:19].replace("T"," ")
            hitl = " [HITL]" if e.get("human_review_required") else ""
            st.markdown(f"`{ts}` **{e.get('node','?')}**{hitl} -- {e.get('action','')} *(actor: {e.get('actor','')})*")
        steps = result.get("completed_steps",[])
        if steps: st.markdown("Steps: " + " -> ".join(steps))

if __name__ == "__main__":
    main()
