"""
Structural tests for the clinical_trial_ops.asl.json Step Functions definition.
No AWS credentials required.
"""
from __future__ import annotations

import json
import os
import pytest

ASL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "stepfunctions",
    "clinical_trial_ops.asl.json",
)


@pytest.fixture(scope="module")
def asl():
    with open(ASL_PATH) as f:
        return json.load(f)


def test_asl_loads(asl):
    assert isinstance(asl, dict)


def test_start_at_assemble(asl):
    assert asl["StartAt"] == "Assemble"


def test_required_states_present(asl):
    states = asl["States"]
    for name in ("Assemble", "Draft", "Check", "RouteDecision", "HumanReviewGate", "Finalize"):
        assert name in states, f"Missing state: {name}"


def test_hitl_gate_uses_wait_for_task_token(asl):
    hitl = asl["States"]["HumanReviewGate"]
    assert hitl["Type"] == "Task"
    resource = hitl["Resource"]
    assert "waitForTaskToken" in resource


def test_hitl_gate_has_timeout(asl):
    hitl = asl["States"]["HumanReviewGate"]
    assert "TimeoutSeconds" in hitl
    # Must be at least 1 hour
    assert hitl["TimeoutSeconds"] >= 3600


def test_route_decision_is_choice(asl):
    rd = asl["States"]["RouteDecision"]
    assert rd["Type"] == "Choice"


def test_route_decision_has_draft_and_hitl_branches(asl):
    choices = asl["States"]["RouteDecision"]["Choices"]
    targets = {c["Next"] for c in choices}
    assert "Draft" in targets
    assert "HumanReviewGate" in targets


def test_failure_states_present(asl):
    states = asl["States"]
    fail_states = [s for s, v in states.items() if v.get("Type") == "Fail"]
    assert len(fail_states) >= 2  # ReviewTimeout + PipelineFailed


def test_finalize_is_end(asl):
    finalize = asl["States"]["Finalize"]
    assert finalize.get("End") is True


def test_assemble_has_retry(asl):
    assert "Retry" in asl["States"]["Assemble"]


def test_draft_has_retry(asl):
    assert "Retry" in asl["States"]["Draft"]


def test_check_has_retry(asl):
    assert "Retry" in asl["States"]["Check"]
