"""Validate the Medical Affairs MSL Step Functions ASL is well-formed and HITL-gated."""
import json
from pathlib import Path


def test_asl_valid_and_has_hitl_gate():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "medical_affairs_msl.asl.json")
        .read_text()
    )
    states = asl["States"]
    assert asl["StartAt"] == "Assemble"
    gate = states["HumanReviewGate"]
    assert gate["Resource"].endswith("waitForTaskToken")
    assert states["Finalize"]["End"] is True
    assert gate["Next"] == "Finalize"


def test_asl_draft_is_revisable():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "medical_affairs_msl.asl.json")
        .read_text()
    )
    states = asl["States"]
    route = states["RouteChoice"]
    choices = route.get("Choices", [])
    draft_targets = [c for c in choices if c.get("Next") == "Draft"]
    assert len(draft_targets) >= 1, "RouteChoice must have a path back to Draft"


def test_asl_has_mlr_comment():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "medical_affairs_msl.asl.json")
        .read_text()
    )
    assert "Comment" in asl
    assert "MLR" in asl["Comment"] or "waitForTaskToken" in asl["Comment"]
