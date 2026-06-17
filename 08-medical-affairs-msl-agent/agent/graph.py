# agent/graph.py
# ============================================================
# LangGraph DAG for the Medical Affairs MSL workflow.
#
#   intake -> pull_hcp_and_content -> enrich_and_validate ->
#   draft_brief -> compliance_check ->
#   [routing] -> { draft_brief (bounded revise, grounding only) |
#                  human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["human_review_gate"].
# Off-label / promotional findings ESCALATE (not REVISE) — they still route
# to human_review_gate so the Approver can see and resolve the finding.
# finalize calls mlr.submit_for_review — HIGH-RISK, requires approval.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    compliance_check,
    draft_brief,
    enrich_and_validate,
    finalize,
    human_review_gate,
    intake,
    pull_hcp_and_content,
    routing_decision,
)
from agent.persistence import get_checkpointer
from agent.state import MedicalAffairsMSLState

logger = logging.getLogger(__name__)


def build_medical_affairs_msl_graph(use_memory: bool = True):
    workflow = StateGraph(MedicalAffairsMSLState)

    workflow.add_node("intake", intake)
    workflow.add_node("pull_hcp_and_content", pull_hcp_and_content)
    workflow.add_node("enrich_and_validate", enrich_and_validate)
    workflow.add_node("draft_brief", draft_brief)
    workflow.add_node("compliance_check", compliance_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "pull_hcp_and_content")
    workflow.add_edge("pull_hcp_and_content", "enrich_and_validate")
    workflow.add_edge("enrich_and_validate", "draft_brief")
    workflow.add_edge("draft_brief", "compliance_check")
    workflow.add_conditional_edges(
        source="compliance_check",
        path=routing_decision,
        path_map={
            "draft_brief": "draft_brief",               # bounded grounding-only revise
            "human_review_gate": "human_review_gate",   # approve or escalate -> human
        },
    )
    workflow.add_edge("human_review_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["human_review_gate"],
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[HCP Meeting Request] --> B[intake<br/>Parse HCP and topic]
    B --> C[pull_hcp_and_content<br/>crm.get_hcp · dms.get_document]
    C --> D[enrich_and_validate<br/>Profile enrich · Doc validate · NBA]
    D --> E[draft_brief<br/>LLM on-label cited brief]
    E --> F[compliance_check<br/>Off-label · Promotional · Grounding]
    F --> G{routing_decision}
    G -->|grounding revise, bounded| E
    G -->|approve or escalate| H[human_review_gate<br/>MEDICAL_AFFAIRS_APPROVER HITL]
    H --> I[finalize<br/>mlr.submit_for_review HIGH-RISK]
    I --> J[END]
    style H fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
"""
