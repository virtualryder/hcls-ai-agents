# agent/graph.py
# ============================================================
# LangGraph DAG for the Pharmacovigilance ICSR Intake workflow.
#
#   intake -> validity_check -> extract_fields -> code_terms ->
#   duplicate_search -> seriousness_assessment -> narrative_draft ->
#   quality_check -> [routing] -> { narrative_draft (revise, bounded) |
#                                   human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: the graph compiles with
# interrupt_before=["human_review_gate"], so a PV Medical Reviewer must update
# state and resume before finalize runs. No application code can bypass it.
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    intake,
    validity_check,
    extract_fields,
    code_terms,
    duplicate_search,
    seriousness_assessment,
    narrative_draft,
    quality_check,
    routing_decision,
    human_review_gate,
    finalize,
)
from agent.persistence import get_checkpointer
from agent.state import PharmacovigilanceState

logger = logging.getLogger(__name__)


def build_pharmacovigilance_graph(use_memory: bool = True):
    workflow = StateGraph(PharmacovigilanceState)

    workflow.add_node("intake", intake)
    workflow.add_node("validity_check", validity_check)
    workflow.add_node("extract_fields", extract_fields)
    workflow.add_node("code_terms", code_terms)
    workflow.add_node("duplicate_search", duplicate_search)
    workflow.add_node("seriousness_assessment", seriousness_assessment)
    workflow.add_node("narrative_draft", narrative_draft)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "validity_check")
    workflow.add_edge("validity_check", "extract_fields")
    workflow.add_edge("extract_fields", "code_terms")
    workflow.add_edge("code_terms", "duplicate_search")
    workflow.add_edge("duplicate_search", "seriousness_assessment")
    workflow.add_edge("seriousness_assessment", "narrative_draft")
    workflow.add_edge("narrative_draft", "quality_check")
    workflow.add_conditional_edges(
        source="quality_check",
        path=routing_decision,
        path_map={
            "narrative_draft": "narrative_draft",        # bounded revision loop
            "human_review_gate": "human_review_gate",   # clean or escalated -> human
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
    A[AE Source Record] --> B[intake<br/>Parse source type]
    B --> C[validity_check<br/>4 ICSR elements]
    C --> D[extract_fields<br/>E2B fields]
    D --> E[code_terms<br/>MedDRA PT · WHODrug]
    E --> F[duplicate_search<br/>Safety DB]
    F --> G[seriousness_assessment<br/>Criteria · Clock]
    G --> H[narrative_draft<br/>CIOMS/E2B narrative]
    H --> I[quality_check<br/>Grounding · PHI · Elements]
    I --> J{routing_decision}
    J -->|issues, revise| H
    J -->|clean / escalate| K[human_review_gate<br/>PV Medical Reviewer]
    K --> L[finalize<br/>Safety DB submit · Deadline]
    L --> M[END]
    style K fill:#4CAF50,color:#fff
    style M fill:#2196F3,color:#fff
"""
