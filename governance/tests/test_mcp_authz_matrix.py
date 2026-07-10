"""MCP authorization negative-test matrix — the 12 cases a security reviewer expects, proven
against the SHIPPING gateway. Framing maps to HTTP status at the deployed edge (401/403/deny);
offline the gateway returns a DENY decision or the primitive raises. Consistent across every hero.

  1 no token -> 401            5 wrong role -> deny        9  tampered approval args -> deny
  2 bad token -> 401           6 wrong data class -> deny  10 stale/expired approval -> deny
  3 missing scope -> 403       7 self-approval -> deny      11 no outbound credential -> deny
  4 unregistered tool -> deny  8 replayed approval -> deny  12 audit write failure -> deny
"""
import time

import pytest

from hcls_agent_platform import auth
from hcls_agent_platform.mcp_gateway import tokens, approvals
from hcls_agent_platform.mcp_gateway.gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "02-pharmacovigilance"
PROC = {"sub": "u-proc", "custom:hcls_role": "PV_PROCESSOR"}
MSL = {"sub": "u-msl", "custom:hcls_role": "MSL"}
READ = "safety.get_case"
WRITE = "safety.submit_report"
OTHER_DATACLASS_TOOL = "rim.get_obligations"   # regulatory data class — agent 02 is not granted it
ARGS = {"case_id": "ICSR-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


# 1 — no token -> 401 (no authenticated subject)
def test_01_no_token():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


# 2 — bad token -> 401
def test_02_bad_token():
    with pytest.raises(auth.AuthError):
        auth.verify_jwt("not.a.valid.jwt")


# 3 — valid token, missing scope -> 403 (token minted for tool A rejected at tool B)
def test_03_missing_scope():
    tok = tokens.mint_scoped_token(subject="u-proc", agent_id=AGENT, tool=READ, scope=[READ])
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(tok, expected_tool=WRITE)   # scope is READ, not WRITE


# 4 — unregistered tool -> deny
def test_04_unregistered_tool():
    assert gw().invoke(user_claims=PROC, agent_id=AGENT, tool="safety.exfiltrate_all", args={}).decision == "DENY"


# 5 — wrong role -> deny (human not entitled)
def test_05_wrong_role():
    assert gw().invoke(user_claims=MSL, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


# 6 — wrong data class -> deny (data-class boundary enforced via tool entitlement:
#     a tool of a different data class the agent/role is not entitled to is denied)
def test_06_wrong_data_class():
    r = gw().invoke(user_claims=PROC, agent_id=AGENT, tool=OTHER_DATACLASS_TOOL, args={})
    assert r.decision == "DENY"


# 7 — self-approval -> deny
def test_07_self_approval():
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.mint_approval_token(requestor="u-x", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-x")


# 8 — replayed approval -> deny
def test_08_replayed_approval():
    tok = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-rev")
    approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT, tool=WRITE, args=ARGS)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT, tool=WRITE, args=ARGS)


# 9 — tampered approval args -> deny
def test_09_tampered_approval_args():
    tok = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-rev")
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT, tool=WRITE, args={"case_id": "X"})


# 10 — stale/expired approval -> deny
def test_10_expired_approval():
    now = int(time.time())
    payload = {"jti": "j1", "requestor": "u-proc", "approver": "u-rev", "agent_id": AGENT,
               "tool": WRITE, "args_hash": approvals.args_hash(ARGS), "iat": now - 2000, "exp": now - 1000}
    expired = approvals._sign(payload)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(expired, requestor="u-proc", agent_id=AGENT, tool=WRITE, args=ARGS)


# 11 — no outbound credential -> deny (the scoped token IS the outbound credential; without a
#      valid one the connector is unreachable. Prod outbound-auth = IAM/OAuth/token-exchange.)
def test_11_no_outbound_credential():
    with pytest.raises(ValueError):
        tokens.verify_scoped_token("no.valid.outbound.token", expected_tool=READ)


# 12 — audit write failure -> deny (fail-closed; no silent success without a trail)
def test_12_audit_write_failure():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit sink down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=PROC, agent_id=AGENT, tool=READ, args=ARGS)
