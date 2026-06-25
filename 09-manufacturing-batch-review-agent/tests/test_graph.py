# tests/test_graph.py — end-to-end graph + framework-enforced HITL for Agent 09.
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "platform_core"))

from agent.graph import build_batch_review_graph
from agent.state import RecommendedAction

_BATCHES = json.loads((_HERE / "data" / "fixtures" / "sample_batches.json").read_text())["batches"]


def _seed(b):
    return {
        "batch_id": b["batch_id"],
        "product": b["product"],
        "raw_batch_record": b["raw_batch_record"],
        "lims_results": b["lims_results"],
        "acting_user_claims": b["acting_user_claims"],
    }


def _run(idx):
    graph = build_batch_review_graph(use_memory=False)
    return graph.invoke(_seed(_BATCHES[idx]))


def test_graph_runs_and_audits():
    out = _run(0)
    assert out["exception_report"], "exception_report must be populated"
    assert out["audit_trail"], "audit_trail must be populated"
    for node in ["intake", "load_batch", "exception_scan", "disposition_draft", "quality_check"]:
        assert node in out["completed_steps"], f"missing step {node}"


def test_clean_batch_is_right_first_time():
    out = _run(0)
    assert out["exception_count"] == 0
    assert out["right_first_time"] is True
    assert out["recommended_action"] == RecommendedAction.RECOMMEND_RELEASE
    assert out["disposition_recommendation"] == "RELEASE"


def test_minor_deviation_recommends_hold_no_critical():
    out = _run(1)
    # one unsigned non-critical step (MINOR) + one out-of-limit param (MAJOR)
    assert out["exception_count"] >= 2
    assert out["critical_count"] == 0
    assert out["has_open_exceptions"] is True
    assert out["recommended_action"] == RecommendedAction.RECOMMEND_HOLD
    assert out["disposition_recommendation"] == "HOLD"


def test_oos_batch_escalates_with_criticals():
    out = _run(2)
    # OOS assay (CRITICAL) + missing required step S3 (CRITICAL) + blend OOL critical step
    assert out["critical_count"] >= 2
    codes = {e["code"] for e in out["exceptions"]}
    assert "OOS" in codes and "MISSING_STEP" in codes
    assert out["recommended_action"] == RecommendedAction.ESCALATE


def test_report_is_grounded():
    out = _run(2)
    assert out["grounding_report"].get("grounded", True) is True
    assert out["required_elements_present"] is True


def test_hitl_gate_interrupts_before_finalize():
    graph = build_batch_review_graph(use_memory=True)
    cfg = {"configurable": {"thread_id": "t-09-hitl"}}
    graph.invoke(_seed(_BATCHES[0]), cfg)
    snap = graph.get_state(cfg)
    # execution must pause at the QA gate; finalize must NOT have run
    assert snap.next == ("human_review_gate",), f"expected pause at gate, got {snap.next}"
    assert "finalize" not in snap.values.get("completed_steps", [])
    assert snap.values.get("batch_status") != "RELEASED"
