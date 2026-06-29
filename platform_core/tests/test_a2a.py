"""Tests for the reference A2A pattern — the governance invariants must hold."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcls_agent_platform.a2a import A2ASupervisor, A2ARequest

PV_PROCESSOR = {"sub": "u-pv-1", "custom:hcls_role": "PV_PROCESSOR"}
PV_REVIEWER = {"sub": "u-md-7", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}


def test_a2a_read_propagates_identity_and_allows():
    sup = A2ASupervisor("orchestrator")
    res = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                  user_claims=PV_PROCESSOR, tool="safety.get_case",
                                  args={"case_id": "ICSR-1"}, task="triage"))
    assert res.gateway.decision == "ALLOW"
    # A2A dispatch was recorded with the supervisor as on_behalf_of (lineage only).
    disp = [r for r in sup.audit_records() if r.get("decision") == "A2A_DISPATCH"]
    assert disp and disp[-1]["on_behalf_of"] == "orchestrator"
    assert disp[-1]["agent_id"] == "02-pharmacovigilance"
    assert disp[-1]["session_id"] == res.session_id


def test_supervisor_cannot_widen_human_permissions():
    # The human is only a PV_PROCESSOR (not entitled to submit_report). Even though
    # a supervisor initiates the hop, least-privilege intersection still denies it.
    sup = A2ASupervisor("orchestrator")
    res = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                  user_claims=PV_PROCESSOR, tool="safety.submit_report"))
    assert res.gateway.decision == "DENY"


def test_high_risk_via_a2a_still_requires_human_approval():
    # Entitled human (reviewer), high-risk tool, no approval -> PENDING_APPROVAL.
    sup = A2ASupervisor("orchestrator")
    pending = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                      user_claims=PV_REVIEWER, tool="safety.write_case_draft",
                                      args={"case_id": "ICSR-1"}))
    assert pending.gateway.decision == "PENDING_APPROVAL"
    # With a verified human approval bound, it proceeds.
    ok = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                 user_claims=PV_REVIEWER, tool="safety.write_case_draft",
                                 args={"case_id": "ICSR-1"},
                                 approval={"approved": True, "reviewer": {"sub": "u-md-7"}}))
    assert ok.gateway.decision == "ALLOW"


def test_a2a_hop_must_carry_human_identity_not_supervisor():
    sup = A2ASupervisor("orchestrator")
    # No human sub -> fail closed (cannot run on the supervisor's own identity).
    res = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                  user_claims={"custom:hcls_role": "PV_MEDICAL_REVIEWER"},
                                  tool="safety.get_case"))
    assert res.gateway.decision == "DENY"


def test_specialist_cannot_exceed_its_own_grants_via_a2a():
    # Even an entitled regulatory approver cannot make the PV specialist touch RIM:
    # the specialist (02) is not granted rim.* (agent over-reach denied).
    sup = A2ASupervisor("orchestrator")
    res = sup.dispatch(A2ARequest(specialist_id="02-pharmacovigilance",
                                  user_claims={"sub": "u-ra-1", "custom:hcls_role": "REGULATORY_APPROVER"},
                                  tool="rim.create_submission_draft"))
    assert res.gateway.decision == "DENY"
