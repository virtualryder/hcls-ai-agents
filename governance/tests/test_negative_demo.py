"""CI gate for the 10-point negative demo (demo/negative_demo.py). Every refusal must fire —
a regression that lets any of the 10 through fails the build. No network; fixture connector."""
import importlib.util
import os

import pytest

from hcls_agent_platform import auth, budget
from hcls_agent_platform.mcp_gateway import approvals
from hcls_agent_platform.mcp_gateway import audit as audit_mod
from hcls_agent_platform.mcp_gateway.gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "02-pharmacovigilance"
PROC = {"sub": "u-proc", "custom:hcls_role": "PV_PROCESSOR"}
MSL = {"sub": "u-msl", "custom:hcls_role": "MSL"}
ARGS = {"case_id": "ICSR-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_1_no_jwt_denied():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool="safety.get_case", args=ARGS).decision == "DENY"


def test_2_bad_jwt_denied():
    with pytest.raises(auth.AuthError):
        auth.verify_jwt("eyJhbGciOiJub25lIn0.bad.sig")


def test_3_wrong_role_denied():
    assert gw().invoke(user_claims=MSL, agent_id=AGENT, tool="safety.get_case", args=ARGS).decision == "DENY"


def test_4_unregistered_tool_denied():
    assert gw().invoke(user_claims=PROC, agent_id=AGENT, tool="safety.exfiltrate_all", args={}).decision == "DENY"


def test_5_self_approval_denied():
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.mint_approval_token(requestor="u-rev", agent_id=AGENT,
                                      tool="safety.submit_report", args=ARGS, approver="u-rev")


def test_6_replay_denied():
    tok = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args=ARGS, approver="u-rev")
    approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT,
                                    tool="safety.submit_report", args=ARGS)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args=ARGS)


def test_7_tampered_args_denied():
    tok = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args=ARGS, approver="u-rev")
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args={"case_id": "X"})


def test_8_masking_failure_fail_closed():
    log = GatewayAuditLog()
    orig = audit_mod.mask
    audit_mod.mask = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("masker down"))
    try:
        with pytest.raises(Exception):
            log.record({"decision": "ALLOW", "tool": "safety.get_case",
                        "args": {"note": "SSN 123-45-6789"}})
        assert log.records == []          # nothing unmasked was persisted
    finally:
        audit_mod.mask = orig


def test_9_audit_write_failure_fail_closed():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=PROC, agent_id=AGENT, tool="safety.get_case", args=ARGS)


def test_10_budget_exceeded_denied():
    m = budget.BudgetMeter(agent_id=AGENT, dept="PV", monthly_token_cap=1000, cap_behavior="hard")
    m.commit(900)
    assert m.preflight(500).allowed is False


def test_demo_script_exits_zero():
    """The runnable demo returns 0 only when all 10 refusals fire."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "demo", "negative_demo.py")
    spec = importlib.util.spec_from_file_location("negdemo", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
