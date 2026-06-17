"""
Regulatory Writing Agent — Streamlit demo dashboard.

Showcases the full workflow: intake -> regulatory intelligence -> evidence ->
draft -> compliance/grounding checks -> human review gate -> finalize. Runs with
no API key in EXTRACT_MODE=demo. The human-in-the-loop sign-off is explicit:
nothing is "finalized" until a Regulatory Approver approves in the UI.
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

from agent.graph import build_regulatory_writing_graph
from agent.state import RecommendedAction

st.set_page_config(page_title="Regulatory Writing Agent", page_icon="📑", layout="wide")

ROLES = ["REGULATORY_AUTHOR", "REGULATORY_APPROVER"]


def load_requests():
    f = HERE / "data" / "fixtures" / "sample_requests.json"
    return json.loads(f.read_text())["requests"]


# ── Sidebar: identity + config ────────────────────────────────────────────────
st.sidebar.title("📑 Regulatory Writing Agent")
st.sidebar.caption("AI-assisted regulatory authoring — human approves every submission.")
role = st.sidebar.selectbox("Acting role (from your IdP)", ROLES, index=0)
user_sub = st.sidebar.text_input("User ID", value="demo.user")
os.environ.setdefault("EXTRACT_MODE", "demo")
st.sidebar.info(f"Mode: **{os.getenv('EXTRACT_MODE','demo')}** · Connectors: "
                f"**{os.getenv('CONNECTOR_MODE','fixture')}**")

requests = load_requests()
labels = [f"{r['request_id']} — {r['document_type']} ({r['product']})" for r in requests]
choice = st.sidebar.selectbox("Authoring request", range(len(requests)), format_func=lambda i: labels[i])
req = requests[choice]

st.title("Regulatory Submission Drafting")
st.write(f"**{req['document_type']}** · {req['product']} · {req['indication']} · "
         f"target: {req['target_authority']} · {req['section_ref']}")

tab_run, tab_evidence, tab_audit = st.tabs(["Draft & Review", "Evidence", "Audit Trail"])

if "result" not in st.session_state:
    st.session_state.result = None

with tab_run:
    if st.button("▶ Run drafting workflow", type="primary"):
        seed = {
            **{k: req[k] for k in ("request_id", "document_type", "product", "indication",
                                   "target_authority", "section_ref", "instructions")},
            "acting_user_claims": {"sub": user_sub, "custom:hcls_role": role},
            "study_data": req.get("study_data", {}),
            "source_documents": req.get("source_documents", []),
        }
        graph = build_regulatory_writing_graph(use_memory=False)
        with st.spinner("Assembling evidence and drafting…"):
            st.session_state.result = graph.invoke(seed)

    res = st.session_state.result
    if res:
        action = res.get("recommended_action")
        color = {RecommendedAction.APPROVE_DRAFT: "green",
                 RecommendedAction.REVISE: "orange",
                 RecommendedAction.ESCALATE: "red"}.get(action, "gray")
        st.markdown(f"**Disposition:** :{color}[{getattr(action,'value',action)}] · "
                    f"drafted by `{res.get('drafted_by')}` · status `{res.get('case_status')}`")

        st.subheader("Drafted section")
        st.write(res.get("draft_text", ""))

        g = res.get("grounding_report", {})
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Grounded", "✅ yes" if g.get("grounded") else "⚠ review")
            if not g.get("grounded"):
                st.warning(f"Ungrounded numbers: {g.get('ungrounded_numbers')}\n\n"
                           f"Ungrounded entities: {g.get('ungrounded_entities')}")
        with c2:
            comp = res.get("compliance_findings", [])
            st.metric("Compliance findings", len(comp))
            for f in comp:
                st.error(f)

        st.divider()
        st.subheader("👤 Human review gate (Regulatory Approver)")
        if role != "REGULATORY_APPROVER":
            st.info("Switch acting role to REGULATORY_APPROVER to authorize the submission draft.")
        else:
            st.checkbox("I have reviewed the draft, grounding report, and compliance findings.")
            if st.button("✅ Approve & create submission draft (RIM)"):
                st.success("Approval recorded with your verified identity. In a live deployment "
                           "the gateway mints a scoped token and creates the RIM draft (audited).")

with tab_evidence:
    st.subheader("Structured facts (grounding corpus)")
    st.json(req.get("study_data", {}))
    st.subheader("Source documents")
    for d in req.get("source_documents", []):
        st.markdown(f"**{d.get('title')}** (v{d.get('version')}, {d.get('status')})")
        st.caption(d.get("text", ""))

with tab_audit:
    res = st.session_state.result
    if res and res.get("audit_trail"):
        st.subheader("Audit trail (21 CFR Part 11)")
        st.dataframe(res["audit_trail"], use_container_width=True)
    else:
        st.info("Run the workflow to populate the audit trail.")

st.caption("Decision-support tool. All AI output requires review and approval by a qualified "
           "Regulatory Approver before any submission. The AI never files with a health authority.")
