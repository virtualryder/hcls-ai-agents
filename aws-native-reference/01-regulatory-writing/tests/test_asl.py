"""Validate the Step Functions ASL is well-formed and HITL-gated."""
import json
from pathlib import Path


def test_asl_valid_and_has_hitl_gate():
    asl = json.loads((Path(__file__).resolve().parent.parent / "stepfunctions" /
                      "regulatory_writing.asl.json").read_text())
    states = asl["States"]
    assert asl["StartAt"] == "Assemble"
    # Human gate must use waitForTaskToken (framework-enforced HITL).
    gate = states["HumanReviewGate"]
    assert gate["Resource"].endswith("waitForTaskToken")
    # Finalize is terminal and only reachable after the gate.
    assert states["Finalize"]["End"] is True
    assert gate["Next"] == "Finalize"
