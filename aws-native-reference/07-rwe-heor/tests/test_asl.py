"""Validate the RWE/HEOR Step Functions ASL is well-formed and HITL-gated."""
import json
from pathlib import Path


def test_asl_valid_and_has_hitl_gate():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "rwe_heor.asl.json")
        .read_text()
    )
    states = asl["States"]
    assert asl["StartAt"] == "Assemble"
    # Human gate must use waitForTaskToken (framework-enforced HITL)
    gate = states["HumanReviewGate"]
    assert gate["Resource"].endswith("waitForTaskToken")
    # Finalize is terminal and only reachable after the gate
    assert states["Finalize"]["End"] is True
    assert gate["Next"] == "Finalize"


def test_asl_synthesis_is_revisable():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "rwe_heor.asl.json")
        .read_text()
    )
    states = asl["States"]
    route = states["RouteChoice"]
    # RouteChoice must be able to loop back to Synthesize
    choices = route.get("Choices", [])
    synthesize_targets = [c for c in choices if c.get("Next") == "Synthesize"]
    assert len(synthesize_targets) >= 1, "RouteChoice must have a path back to Synthesize"


def test_asl_has_comment():
    asl = json.loads(
        (Path(__file__).resolve().parent.parent / "stepfunctions" / "rwe_heor.asl.json")
        .read_text()
    )
    assert "Comment" in asl
    assert "HITL" in asl["Comment"] or "waitForTaskToken" in asl["Comment"]
