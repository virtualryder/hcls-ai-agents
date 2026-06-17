# agent/graph.py
# ============================================================
# LangGraph DAG for the Quality CAPA workflow.
#
#   intake -> classify_event -> search_similar_events ->
#   root_cause_analysis -> draft_capa -> quality_check ->
#   [routing] -> { draft_capa | human_review_gate } -> finalize -> END
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    classify_event,
    draft_capa,
    finalize,
    human_review_gate,
    intake,
    quality_check,
    root_cause_analysis,
    routing_decision,
    search_similar_events,
)
from agent.persistence import get_checkpointer
from agent.state import QualityCAPAState

logger = logging.getLogger(__name__)


def build_quality_capa_graph(use_memory: bool = True):
    workflow = StateGraph(QualityCAPAState)

    workflow.add_node("intake", intake)
    workflow.add_node("classify_event", classify_event)
    workflow.add_node("search_similar_events", search_similar_events)
    workflow.add_node("root_cause_analysis", root_cause_analysis)
    workflow.add_node("draft_capa", draft_capa)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "classify_event")
    workflow.add_edge("classify_event", "search_similar_events")
    workflow.add_edge("search_similar_events", "root_cause_analysis")
    workflow.add_edge("root_cause_analysis", "draft_capa")
    workflow.add_edge("draft_capa", "quality_check")
    workflow.add_conditional_edges(
        source="quality_check",
        path=routing_decision,
        path_map={
            "draft_capa": "draft_capa",
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


def get_graph_visualization() -> str:
    return """
graph TD
    A[Complaint / Deviation] --> B[intake<br/>Parse event]
    B --> C[classify_event<br/>QMS · Risk level]
    C --> D[search_similar_events<br/>Trend · Cluster]
    D --> E[root_cause_analysis<br/>Hypotheses]
    E --> F[draft_capa<br/>LLM CAPA plan]
    F --> G[quality_check<br/>GMP · Grounding]
    G --> H{routing_decision}
    H -->|revise| F
    H -->|approve / escalate| I[human_review_gate<br/>Qualified Person]
    I --> J[finalize<br/>QMS CAPA draft created]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
