# agent/graph.py
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    estimate_cohorts,
    fairness_review,
    finalize,
    human_review_gate,
    intake,
    rank_sites,
    routing_decision,
    run_cohort_query,
    translate_criteria,
)
from agent.persistence import get_checkpointer
from agent.state import SitePatientMatchingState

logger = logging.getLogger(__name__)


def build_site_patient_matching_graph(use_memory: bool = True):
    workflow = StateGraph(SitePatientMatchingState)

    workflow.add_node("intake", intake)
    workflow.add_node("translate_criteria", translate_criteria)
    workflow.add_node("run_cohort_query", run_cohort_query)
    workflow.add_node("estimate_cohorts", estimate_cohorts)
    workflow.add_node("rank_sites", rank_sites)
    workflow.add_node("fairness_review", fairness_review)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "translate_criteria")
    workflow.add_edge("translate_criteria", "run_cohort_query")
    workflow.add_edge("run_cohort_query", "estimate_cohorts")
    workflow.add_edge("estimate_cohorts", "rank_sites")
    workflow.add_edge("rank_sites", "fairness_review")
    workflow.add_conditional_edges(
        source="fairness_review",
        path=routing_decision,
        path_map={
            "rank_sites": "rank_sites",
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
    A[Matching Request] --> B[intake]
    B --> C[translate_criteria]
    C --> D[run_cohort_query]
    D --> E[estimate_cohorts]
    E --> F[rank_sites]
    F --> G[fairness_review]
    G --> H{routing_decision}
    H -->|revise| F
    H -->|approve / escalate| I[human_review_gate]
    I --> J[finalize]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
