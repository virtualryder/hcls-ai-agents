# agent/graph.py
# ============================================================
# LangGraph DAG for the RWE/HEOR workflow.
#
#   intake -> define_cohort -> run_cohort_query -> assess_data_quality ->
#   synthesize_evidence -> grounding_check ->
#   [routing] -> { synthesize_evidence (bounded revise) |
#                  human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["human_review_gate"] means an
# Epidemiologist must update state and resume before finalize runs.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    assess_data_quality,
    define_cohort,
    finalize,
    grounding_check,
    human_review_gate,
    intake,
    routing_decision,
    run_cohort_query,
    synthesize_evidence,
)
from agent.persistence import get_checkpointer
from agent.state import RWEHEORState

logger = logging.getLogger(__name__)


def build_rwe_heor_graph(use_memory: bool = True):
    workflow = StateGraph(RWEHEORState)

    workflow.add_node("intake", intake)
    workflow.add_node("define_cohort", define_cohort)
    workflow.add_node("run_cohort_query", run_cohort_query)
    workflow.add_node("assess_data_quality", assess_data_quality)
    workflow.add_node("synthesize_evidence", synthesize_evidence)
    workflow.add_node("grounding_check", grounding_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "define_cohort")
    workflow.add_edge("define_cohort", "run_cohort_query")
    workflow.add_edge("run_cohort_query", "assess_data_quality")
    workflow.add_edge("assess_data_quality", "synthesize_evidence")
    workflow.add_edge("synthesize_evidence", "grounding_check")
    workflow.add_conditional_edges(
        source="grounding_check",
        path=routing_decision,
        path_map={
            "synthesize_evidence": "synthesize_evidence",   # bounded revision loop
            "human_review_gate": "human_review_gate",       # clean / escalate -> human
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
    A[RWE Research Request] --> B[intake<br/>Parse question and context]
    B --> C[define_cohort<br/>Computable ICD-10 spec]
    C --> D[run_cohort_query<br/>rwd.run_cohort_query gateway]
    D --> E[assess_data_quality<br/>Completeness · Balance · Confounding]
    E --> F[synthesize_evidence<br/>LLM narrative from validated stats]
    F --> G[grounding_check<br/>Numbers traceable · No causal claims]
    G --> H{routing_decision}
    H -->|revise, bounded| F
    H -->|clean / escalate| I[human_review_gate<br/>EPIDEMIOLOGIST HITL]
    I --> J[finalize<br/>Lock audit trail]
    J --> K[END]
    style I fill:#4CAF50,color:#fff
    style K fill:#2196F3,color:#fff
"""
