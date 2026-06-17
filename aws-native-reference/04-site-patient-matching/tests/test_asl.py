"""Structural tests for site_patient_matching.asl.json."""
from __future__ import annotations
import json, os, pytest

ASL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "stepfunctions", "site_patient_matching.asl.json"
)

@pytest.fixture(scope="module")
def asl():
    with open(ASL_PATH) as f:
        return json.load(f)

def test_asl_loads(asl): assert isinstance(asl, dict)
def test_start_at_assemble(asl): assert asl["StartAt"] == "Assemble"

def test_required_states_present(asl):
    for name in ("Assemble", "Draft", "Check", "RouteDecision", "HumanReviewGate", "Finalize"):
        assert name in asl["States"], f"Missing: {name}"

def test_hitl_uses_wait_for_task_token(asl):
    hitl = asl["States"]["HumanReviewGate"]
    assert hitl["Type"] == "Task"
    assert "waitForTaskToken" in hitl["Resource"]

def test_hitl_has_timeout(asl):
    hitl = asl["States"]["HumanReviewGate"]
    assert "TimeoutSeconds" in hitl
    assert hitl["TimeoutSeconds"] >= 3600

def test_route_decision_is_choice(asl):
    assert asl["States"]["RouteDecision"]["Type"] == "Choice"

def test_route_has_draft_and_hitl_branches(asl):
    choices = asl["States"]["RouteDecision"]["Choices"]
    targets = {c["Next"] for c in choices}
    assert "Draft" in targets and "HumanReviewGate" in targets

def test_failure_states_present(asl):
    fails = [s for s, v in asl["States"].items() if v.get("Type") == "Fail"]
    assert len(fails) >= 2

def test_finalize_is_end(asl):
    assert asl["States"]["Finalize"].get("End") is True

def test_assemble_has_retry(asl): assert "Retry" in asl["States"]["Assemble"]
def test_draft_has_retry(asl): assert "Retry" in asl["States"]["Draft"]
def test_check_has_retry(asl): assert "Retry" in asl["States"]["Check"]
