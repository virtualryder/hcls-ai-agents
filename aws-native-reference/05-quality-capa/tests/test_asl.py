"""Validate the Step Functions ASL is well-formed and HITL-gated."""
import json
from pathlib import Path


def test_asl_valid_and_has_hitl_gate():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "quality_capa.asl.json").read_text()
    )
    states = asl["States"]
    assert asl["StartAt"] == "Assemble"
    # Human gate must use waitForTaskToken (framework-enforced HITL).
    gate = states["HumanReviewGate"]
    assert gate["Resource"].endswith("waitForTaskToken")
    # Finalize is terminal and only reachable after the gate.
    assert states["Finalize"]["End"] is True
    assert gate["Next"] == "Finalize"


def test_asl_has_revision_loop():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "quality_capa.asl.json").read_text()
    )
    states = asl["States"]
    # RouteChoice must have a choice that loops back to Draft
    route = states["RouteChoice"]
    assert route["Type"] == "Choice"
    choices = route["Choices"]
    back_to_draft = any(c.get("Next") == "Draft" for c in choices)
    assert back_to_draft, "RouteChoice must have a path back to Draft for revision"


def test_asl_default_routes_to_hitl():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "quality_capa.asl.json").read_text()
    )
    states = asl["States"]
    route = states["RouteChoice"]
    assert route.get("Default") == "HumanReviewGate"
