"""
Manufacturing Batch-Review Agent — Streamlit demo dashboard.

Showcases the full workflow: intake -> load_batch -> exception_scan ->
disposition_draft -> quality_check -> human_review_gate -> finalize. Runs with no
API key in EXTRACT_MODE=demo. Nothing is released/held until a QA reviewer signs
off in the UI — the HITL gate is framework-enforced (interrupt_before).
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

from agent.graph import build_batch_review_graph
from agent.state import RecommendedAction

st.set_page_config(page_title="Manufacturing Batch-Review Agent", page_icon="🏭", layout="wide")

_BATCHES = json.loads((HERE / "data" / "fixtures" / "sample_batches.json").read_text())["batches"]


def _seed(b):
    return {
        "batch_id": b["batch_id"], "product": b["product"],
        "raw_batch_record": b["raw_batch_record"], "lims_results": b["lims_results"],
        "acting_user_claims": b["acting_user_claims"],
    }


st.title("🏭 Manufacturing Batch-Review Agent")
st.caption("Review by exception · QA owns every release/reject · 21 CFR Part 11 audit · "
           "demo mode (no API key)")

with st.sidebar:
    st.header("Select a batch")
    labels = [f"{b['batch_id']} — {b['product']}" for b in _BATCHES]
    idx = st.radio("Batch record", range(len(labels)), format_func=lambda i: labels[i])
    run = st.button("Review batch", type="primary")
    st.markdown("---")
    st.markdown("**The bright line:** the agent reviews records and flags exceptions; "
                "a QA reviewer makes and signs the release/reject decision.")

if run:
    graph = build_batch_review_graph(use_memory=True)
    cfg = {"configurable": {"thread_id": f"ui-{_BATCHES[idx]['batch_id']}"}}
    state = graph.invoke(_seed(_BATCHES[idx]), cfg)  # pauses at human_review_gate

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Exceptions", state.get("exception_count", 0))
    c2.metric("Critical", state.get("critical_count", 0))
    c3.metric("Right-first-time", "Yes" if state.get("right_first_time") else "No")
    c4.metric("Recommendation", state.get("disposition_recommendation", "—"))

    st.subheader("Exception report (draft for QA)")
    st.info(state.get("exception_report", ""))

    if state.get("exceptions"):
        st.subheader("Exceptions (review by exception)")
        st.dataframe(state["exceptions"], use_container_width=True)
    else:
        st.success("No exceptions found — batch is right-first-time.")

    st.subheader("⏸️ Human gate — QA reviewer sign-off (framework-enforced)")
    snap = graph.get_state(cfg)
    st.warning(f"Execution paused at: {snap.next}. Nothing is released until QA signs.")
    decision = st.radio("QA decision", ["RELEASE", "HOLD"],
                        index=0 if state.get("disposition_recommendation") == "RELEASE" else 1)
    reviewer = st.text_input("QA reviewer (bound as e-signature)", "qa.reviewer@demo")
    if st.button("Sign disposition"):
        approval = {"approved_by": reviewer, "decision": decision,
                    "reviewer_claims": {"sub": reviewer, "custom:hcls_role": "QA_RELEASE"}}
        graph.update_state(cfg, {"approval": approval,
                                 "acting_user_claims": approval["reviewer_claims"]})
        final = graph.invoke(None, cfg)
        st.success(f"Batch status: {final.get('batch_status')} · "
                   f"disposition {final.get('disposition_id', 'PENDING')}")
        with st.expander("Audit trail (21 CFR Part 11)"):
            st.json(final.get("audit_trail", []))
else:
    st.info("Select a batch and click **Review batch**. "
            "Batch B-24-0417 is clean (release), B-24-0418 has minor deviations (hold), "
            "B-24-0419 is OOS (escalate).")
