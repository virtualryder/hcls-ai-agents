# agent/graph.py
# ============================================================
# LangGraph DAG for the Regulatory Writing workflow.
#
#   intake -> regulatory_intelligence -> evidence_assembly -> draft_section ->
#   consistency_check -> [routing] -> { draft_section (revise, bounded) |
#                                       human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: the graph compiles with
# interrupt_before=["human_review_gate"], so a Regulatory Approver must update
# state and resume before finalize runs. No application code can bypass it.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    consistency_check,
    draft_section,
    evidence_assembly,
    finalize,
    human_review_gate,
    intake,
    regulatory_intelligence_node,
    routing_decision,
)
from agent.persistence import get_checkpointer
from agent.state import RegulatoryWritingState

logger = logging.getLogger(__name__)


def build_regulatory_writing_graph(use_memory: bool = True):
    workflow = StateGraph(RegulatoryWritingState)

    workflow.add_node("intake", intake)
    workflow.add_node("regulatory_intelligence", regulatory_intelligence_node)
    workflow.add_node("evidence_assembly", evidence_assembly)
    workflow.add_node("draft_section", draft_section)
    workflow.add_node("consistency_check", consistency_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "regulatory_intelligence")
    workflow.add_edge("regulatory_intelligence", "evidence_assembly")
    workflow.add_edge("evidence_assembly", "draft_section")
    workflow.add_edge("draft_section", "consistency_check")
    workflow.add_conditional_edges(
        source="consistency_check",
        path=routing_decision,
        path_map={
            "draft_section": "draft_section",          # bounded revision loop
            "human_review_gate": "human_review_gate",  # clean or escalated -> human
        },
    )
    workflow.add_edge("human_review_gate", "finalize")
    workflow.add_edge("finalize", END)

    if use_memory:
        return workflow.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["human_review_gate"],  # framework-enforced HITL
        )
    return workflow.compile()


def get_graph_visualization() -> str:
    return """
graph TD
    A[Authoring Request] --> B[intake<br/>Parse request & scope]
    B --> C[regulatory_intelligence<br/>Obligations · Guidance]
    C --> D[evidence_assembly<br/>Source docs · Study data]
    D --> E[draft_section<br/>LLM draft - grounded]
    E --> F[consistency_check<br/>Compliance · Grounding]
    F --> G{routing_decision}
    G -->|issues, revise| E
    G -->|clean / escalate| H[human_review_gate<br/>Regulatory Approver]
    H --> I[finalize<br/>RIM draft · Audit trail]
    I --> J[END]
    style H fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
"""
