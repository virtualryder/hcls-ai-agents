"""
Structural tests for the pharmacovigilance.asl.json Step Functions definition.
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
    "pharmacovigilance.asl.json",
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
    for name in ("Assemble", "Draft", "Check", "RouteChoice", "HumanReviewGate", "Finalize"):
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


def test_route_choice_is_choice_state(asl):
    rc = asl["States"]["RouteChoice"]
    assert rc["Type"] == "Choice"


def test_route_choice_has_draft_branch(asl):
    choices = asl["States"]["RouteChoice"]["Choices"]
    targets = {c["Next"] for c in choices}
    assert "Draft" in targets


def test_route_choice_has_hitl_branch(asl):
    choices = asl["States"]["RouteChoice"]["Choices"]
    targets = {c["Next"] for c in choices}
    assert "HumanReviewGate" in targets


def test_failure_states_present(asl):
    states = asl["States"]
    fail_states = [s for s, v in states.items() if v.get("Type") == "Fail"]
    assert len(fail_states) >= 2, f"Expected at least 2 Fail states, found: {fail_states}"


def test_finalize_is_terminal(asl):
    finalize = asl["States"]["Finalize"]
    assert finalize.get("End") is True


def test_hitl_gate_leads_to_finalize(asl):
    hitl = asl["States"]["HumanReviewGate"]
    assert hitl["Next"] == "Finalize"


def test_assemble_has_retry(asl):
    assert "Retry" in asl["States"]["Assemble"]


def test_draft_has_retry(asl):
    assert "Retry" in asl["States"]["Draft"]


def test_check_has_retry(asl):
    assert "Retry" in asl["States"]["Check"]


def test_hitl_gate_catches_timeout(asl):
    hitl = asl["States"]["HumanReviewGate"]
    catch_errors = {e for c in hitl.get("Catch", []) for e in c["ErrorEquals"]}
    assert "States.HeartbeatTimeout" in catch_errors or "States.Timeout" in catch_errors
