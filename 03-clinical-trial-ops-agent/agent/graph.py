# agent/graph.py
# ============================================================
# LangGraph DAG for the Clinical Trial Ops workflow.
#
#   intake -> pull_study_data -> analyze_tmf -> detect_issues ->
#   draft_queries -> draft_briefing -> quality_check ->
#   [routing] -> { draft_briefing (revise, bounded) |
#                  human_review_gate } -> finalize -> END
#
# HITL is framework-enforced: interrupt_before=["human_review_gate"].
# ============================================================
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    analyze_tmf,
    detect_issues,
    draft_briefing,
    draft_queries,
    finalize,
    human_review_gate,
    intake,
    pull_study_data,
    quality_check,
    routing_decision,
)
from agent.persistence import get_checkpointer
from agent.state import ClinicalTrialOpsState

logger = logging.getLogger(__name__)


def build_clinical_trial_ops_graph(use_memory: bool = True):
    workflow = StateGraph(ClinicalTrialOpsState)

    workflow.add_node("intake", intake)
    workflow.add_node("pull_study_data", pull_study_data)
    workflow.add_node("analyze_tmf", analyze_tmf)
    workflow.add_node("detect_issues", detect_issues)
    workflow.add_node("draft_queries", draft_queries)
    workflow.add_node("draft_briefing", draft_briefing)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "pull_study_data")
    workflow.add_edge("pull_study_data", "analyze_tmf")
    workflow.add_edge("analyze_tmf", "detect_issues")
    workflow.add_edge("detect_issues", "draft_queries")
    workflow.add_edge("draft_queries", "draft_briefing")
    workflow.add_edge("draft_briefing", "quality_check")
    workflow.add_conditional_edges(
        source="quality_check",
        path=routing_decision,
        path_map={
            "draft_briefing": "draft_briefing",        # bounded revision loop
            "human_review_gate": "human_review_gate",  # clean / escalate -> human
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
    A[ClinOps Review Request] --> B[intake]
    B --> C[pull_study_data<br/>CTMS / eTMF / EDC]
    C --> D[analyze_tmf<br/>ICH E6 gap analysis]
    D --> E[detect_issues<br/>Enrollment / Queries / Visits]
    E --> F[draft_queries<br/>EDC query drafts]
    F --> G[draft_briefing<br/>LLM study health brief]
    G --> H[quality_check<br/>Grounding + completeness]
    H --> I{routing_decision}
    I -->|REVISE| G
    I -->|APPROVE / ESCALATE| J[human_review_gate<br/>ClinOps Lead]
    J --> K[finalize<br/>Issue approved EDC queries]
    K --> L[END]
    style J fill:#4CAF50,color:#fff
    style L fill:#2196F3,color:#fff
"""
