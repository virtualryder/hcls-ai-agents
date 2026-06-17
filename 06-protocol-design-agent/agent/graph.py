# agent/graph.py
# ============================================================
# LangGraph DAG for the Protocol Design workflow.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    draft_protocol_sections,
    feasibility_estimate,
    finalize,
    human_review_gate,
    intake,
    quality_check,
    risk_assessment,
    routing_decision,
    search_guidance,
)
from agent.persistence import get_checkpointer
from agent.state import ProtocolDesignState

logger = logging.getLogger(__name__)


def build_protocol_design_graph(use_memory: bool = True):
    workflow = StateGraph(ProtocolDesignState)

    workflow.add_node("intake", intake)
    workflow.add_node("search_guidance", search_guidance)
    workflow.add_node("feasibility_estimate", feasibility_estimate)
    workflow.add_node("draft_protocol_sections", draft_protocol_sections)
    workflow.add_node("risk_assessment", risk_assessment)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "search_guidance")
    workflow.add_edge("search_guidance", "feasibility_estimate")
    workflow.add_edge("feasibility_estimate", "draft_protocol_sections")
    workflow.add_edge("draft_protocol_sections", "risk_assessment")
    workflow.add_edge("risk_assessment", "quality_check")
    workflow.add_conditional_edges(
        source="quality_check",
        path=routing_decision,
        path_map={
            "draft_protocol_sections": "draft_protocol_sections",
            "human_review_gate": "human_review_gate",
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
