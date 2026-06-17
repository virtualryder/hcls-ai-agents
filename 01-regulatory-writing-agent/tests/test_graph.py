"""Integration test: the Regulatory Writing graph runs end-to-end in demo mode."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_regulatory_writing_graph
from agent.state import RecommendedAction


def _seed_state():
    return {
        "request_id": "REQ-TEST",
        "document_type": "BENEFIT_RISK_SUMMARY",
        "product": "Demo-Drug",
        "indication": "type 2 diabetes",
        "target_authority": "FDA",
        "section_ref": "CSR STUDY-301 Section 11",
        "instructions": "Draft benefit-risk summary.",
        "acting_user_claims": {"sub": "u-author", "custom:hcls_role": "REGULATORY_AUTHOR"},
        "study_data": {
            "n_subjects": 450, "primary_endpoint": "HbA1c reduction",
            "hba1c_reduction_pct": 1.2, "comparator": "placebo",
            "source_ref": "CSR STUDY-301 Section 11", "study": "STUDY-301",
        },
        "source_documents": [{"title": "CSR", "version": "1.0", "text": "450 subjects; 1.2 pp."}],
    }


def test_graph_runs_to_human_gate_without_memory():
    # Without a checkpointer the graph runs straight through (no interrupt).
    graph = build_regulatory_writing_graph(use_memory=False)
    out = graph.invoke(_seed_state())
    assert out["draft_text"]
    assert "draft_section" in out["completed_steps"]
    assert "consistency_check" in out["completed_steps"]
    assert out["recommended_action"] in (
        RecommendedAction.APPROVE_DRAFT, RecommendedAction.ESCALATE, RecommendedAction.REVISE
    )
    assert out["audit_trail"], "audit trail must be populated"


def test_clean_draft_recommends_approval():
    graph = build_regulatory_writing_graph(use_memory=False)
    out = graph.invoke(_seed_state())
    # Demo draft is grounded + clean -> APPROVE_DRAFT routed to human gate.
    assert out["recommended_action"] == RecommendedAction.APPROVE_DRAFT
