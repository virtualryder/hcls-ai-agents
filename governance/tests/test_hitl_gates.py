"""
HITL-gate enforcement tests.

Human-in-the-loop is the load-bearing control in every HCLS agent: the AI drafts
and recommends, a qualified human decides. These tests assert the gate is
*framework-enforced* (the gateway refuses high-risk execution without a verified
human approval), not merely documented.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "platform_core"))

from hcls_agent_platform.mcp_gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.policy import HIGH_RISK_TOOLS, CONSEQUENTIAL_COMMITS, AGENT_TOOL_GRANTS, ROLE_ENTITLEMENTS


def _role_for_tool(tool):
    for role, ents in ROLE_ENTITLEMENTS.items():
        if tool in ents:
            return role
    return None


def _agent_for_tool(tool):
    for agent, grants in AGENT_TOOL_GRANTS.items():
        if tool in grants:
            return agent
    return None


def test_every_high_risk_tool_requires_approval():
    gw = MCPGateway()
    for tool in sorted(HIGH_RISK_TOOLS):
        role = _role_for_tool(tool)
        agent = _agent_for_tool(tool)
        # Every high-risk tool must have an entitled human role.
        assert role, f"high-risk tool {tool} lacks an entitled role"
        if tool in CONSEQUENTIAL_COMMITS:
            # Consequential commits are DELIBERATELY withheld from every agent (Phase-2):
            # a human role holds them, but no agent does, so an agent can never invoke them.
            assert agent is None, f"consequential commit {tool} must not be granted to any agent"
            continue
        assert agent, f"high-risk tool {tool} lacks a granting agent"
        claims = {"sub": "u-1", "custom:hcls_role": role}
        res = gw.invoke(user_claims=claims, agent_id=agent, tool=tool, args={})
        assert res.decision == "PENDING_APPROVAL", f"{tool} executed without human approval!"


def test_approval_must_carry_verified_reviewer():
    gw = MCPGateway()
    tool = sorted(HIGH_RISK_TOOLS)[0]
    role, agent = _role_for_tool(tool), _agent_for_tool(tool)
    claims = {"sub": "u-1", "custom:hcls_role": role}
    # Approval flag without a reviewer sub must NOT satisfy the gate.
    res = gw.invoke(user_claims=claims, agent_id=agent, tool=tool, args={},
                    approval={"approved": True, "reviewer": {}})
    assert res.decision == "PENDING_APPROVAL"
    # Proper approval with verified reviewer -> ALLOW.
    ok = gw.invoke(user_claims=claims, agent_id=agent, tool=tool, args={},
                   approval={"approved": True, "reviewer": {"sub": "u-1"}})
    assert ok.decision == "ALLOW"
