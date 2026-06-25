# agent/graph.py
# ============================================================
# LangGraph DAG for the Manufacturing Batch-Review workflow.
#
#   intake -> load_batch -> exception_scan -> disposition_draft ->
#   quality_check -> [routing] -> { disposition_draft (revise, bounded) |
#                                   human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: the graph compiles with
# interrupt_before=["human_review_gate"], so a QA reviewer must update state and
# resume before finalize runs. No application code can bypass it.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    intake,
    load_batch,
    exception_scan,
    disposition_draft,
    quality_check,
    routing_decision,
    human_review_gate,
    finalize,
)
from agent.persistence import get_checkpointer
from agent.state import BatchReviewState

logger = logging.getLogger(__name__)


def build_batch_review_graph(use_memory: bool = True):
    workflow = StateGraph(BatchReviewState)

    workflow.add_node("intake", intake)
    workflow.add_node("load_batch", load_batch)
    workflow.add_node("exception_scan", exception_scan)
    workflow.add_node("disposition_draft", disposition_draft)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "load_batch")
    workflow.add_edge("load_batch", "exception_scan")
    workflow.add_edge("exception_scan", "disposition_draft")
    workflow.add_edge("disposition_draft", "quality_check")
    workflow.add_conditional_edges(
        source="quality_check",
        path=routing_decision,
        path_map={
            "disposition_draft": "disposition_draft",   # bounded revision loop
            "human_review_gate": "human_review_gate",   # clean or escalated -> QA
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
    A[Electronic Batch Record] --> B[intake<br/>Register review]
    B --> C[load_batch<br/>MES EBR + LIMS results]
    C --> D[exception_scan<br/>Limits · OOS · steps · e-sig]
    D --> E[disposition_draft<br/>Exception report + recommendation]
    E --> F[quality_check<br/>Grounding · required elements]
    F --> G{routing_decision}
    G -->|draft issues, revise| E
    G -->|clean / escalate| H[human_review_gate<br/>QA Reviewer]
    H --> I[finalize<br/>MES release/hold · disposition]
    I --> J[END]
    style H fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
"""
