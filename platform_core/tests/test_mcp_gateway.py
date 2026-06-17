"""Tests for the MCP authorization gateway (AgentCore Gateway reference logic)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcls_agent_platform.mcp_gateway import MCPGateway
from hcls_agent_platform.mcp_gateway import policy


AUTHOR = {"sub": "u-author", "custom:hcls_role": "REGULATORY_AUTHOR"}
APPROVER = {"sub": "u-approver", "custom:hcls_role": "REGULATORY_APPROVER"}
PV_PROC = {"sub": "u-pv", "custom:hcls_role": "PV_PROCESSOR"}
PV_MD = {"sub": "u-md", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}


def test_no_subject_denied_fail_closed():
    gw = MCPGateway()
    res = gw.invoke(user_claims={}, agent_id="01-regulatory-writing", tool="rim.get_obligations")
    assert res.decision == "DENY" and not res.allowed


def test_read_allowed_for_entitled_user():
    gw = MCPGateway()
    res = gw.invoke(user_claims=AUTHOR, agent_id="01-regulatory-writing", tool="rim.get_obligations")
    assert res.decision == "ALLOW" and res.result


def test_agent_overreach_denied():
    # PV agent is not granted RIM tools, even if a user were entitled.
    gw = MCPGateway()
    res = gw.invoke(user_claims=APPROVER, agent_id="02-pharmacovigilance", tool="rim.create_submission_draft")
    assert res.decision == "DENY"
    assert "not granted" in res.reason


def test_user_cannot_exceed_entitlement():
    # Author lacks the create_submission_draft entitlement (only approver has it).
    gw = MCPGateway()
    res = gw.invoke(user_claims=AUTHOR, agent_id="01-regulatory-writing", tool="rim.create_submission_draft")
    assert res.decision == "DENY"
    assert "not entitled" in res.reason


def test_high_risk_requires_human_approval():
    gw = MCPGateway()
    # Without approval -> PENDING_APPROVAL
    pending = gw.invoke(user_claims=PV_MD, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                        args={"case_id": "ICSR-DRAFT-0001"})
    assert pending.decision == "PENDING_APPROVAL" and pending.requires_approval
    # With a verified reviewer approval -> ALLOW
    ok = gw.invoke(user_claims=PV_MD, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                   args={"case_id": "ICSR-DRAFT-0001"},
                   approval={"approved": True, "reviewer": {"sub": "u-md"}})
    assert ok.decision == "ALLOW"


def test_processor_cannot_submit_irreversible_report():
    # PV_PROCESSOR is not entitled to safety.submit_report (only PV_MEDICAL_REVIEWER).
    gw = MCPGateway()
    res = gw.invoke(user_claims=PV_PROC, agent_id="02-pharmacovigilance", tool="safety.submit_report")
    assert res.decision == "DENY"


def test_every_agent_grant_tool_is_registered():
    for agent, grants in policy.AGENT_TOOL_GRANTS.items():
        for tool in grants:
            assert tool in policy.TOOL_REGISTRY, f"{agent} grants unregistered tool {tool}"


def test_audit_records_decisions_and_masks_args():
    gw = MCPGateway()
    gw.invoke(user_claims=AUTHOR, agent_id="01-regulatory-writing", tool="dms.get_document",
              args={"note": "patient SSN 123-45-6789"})
    last = gw.audit.records[-1]
    assert last["decision"] in ("ALLOW", "DENY")
    if last["decision"] == "ALLOW":
        assert "123-45-6789" not in str(last["args"])
