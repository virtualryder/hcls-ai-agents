"""CI gate for the end-to-end auth chain shown in demo/demo_auth.py.

Locks in the load-bearing outcomes so a regression in the gateway, policy, token,
or approval modules fails the build. No network; fixture connector only."""
import time

from hcls_agent_platform import auth
from hcls_agent_platform.mcp_gateway import tokens, approvals, policy
from hcls_agent_platform.mcp_gateway.gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

PROC = {"sub": "u-proc", "custom:hcls_role": "PV_PROCESSOR"}
REV = {"sub": "u-rev", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}
MSL = {"sub": "u-msl", "custom:hcls_role": "MSL"}


def _gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_idp_federation_fail_closed():
    assert auth.verify_jwt(PROC)["sub"] == "u-proc"
    assert auth.roles_from_claims(PROC) == ["PV_PROCESSOR"]
    try:
        auth.verify_jwt({"custom:hcls_role": "PV_PROCESSOR"})  # no sub
        assert False, "must fail closed without sub"
    except auth.AuthError:
        pass


def test_token_scoping_deny_paths():
    tok = tokens.mint_scoped_token(subject="u-proc", agent_id="02-pharmacovigilance",
                                   tool="safety.get_case", scope=["safety.get_case"])
    claims = tokens.verify_scoped_token(tok, expected_tool="safety.get_case")
    assert claims["exp"] - claims["iat"] <= 60
    for bad in [
        lambda: tokens.verify_scoped_token(tok, expected_tool="safety.submit_report"),  # confused deputy
        lambda: tokens.verify_scoped_token(tokens._sign({**claims, "exp": int(time.time()) - 5}),
                                           expected_tool="safety.get_case"),             # expired
        lambda: tokens.verify_scoped_token(tok[:-1] + ("0" if tok[-1] != "0" else "1"),
                                           expected_tool="safety.get_case"),             # tampered
    ]:
        try:
            bad(); assert False, "token deny path accepted"
        except ValueError:
            pass


def test_least_privilege_intersection():
    gw = _gw()
    # agent granted AND user entitled -> allow
    assert gw.invoke(user_claims=PROC, agent_id="02-pharmacovigilance",
                     tool="safety.get_case", args={"case_id": "ICSR-1"}).decision == "ALLOW"
    # agent granted but user NOT entitled -> deny (agent may never exceed the human)
    assert gw.invoke(user_claims=MSL, agent_id="02-pharmacovigilance",
                     tool="safety.get_case", args={"case_id": "ICSR-1"}).decision == "DENY"
    # user entitled but agent NOT granted -> deny (over-reach)
    assert gw.invoke(user_claims=REV, agent_id="07-rwe-heor",
                     tool="safety.get_case", args={"case_id": "ICSR-1"}).decision == "DENY"


def test_consequential_commit_withheld_from_every_agent():
    assert "safety.submit_report" in policy.CONSEQUENTIAL_COMMITS
    for grants in policy.AGENT_TOOL_GRANTS.values():
        assert "safety.submit_report" not in grants


def test_separation_of_duties_and_single_use():
    gw = _gw()
    args = {"case_id": "ICSR-1"}
    # no approval -> pending, never auto-allow
    assert gw.invoke(user_claims=REV, agent_id="02-pharmacovigilance",
                     tool="safety.submit_report", args=args).decision == "PENDING_APPROVAL"
    # self-approval refused at mint
    try:
        approvals.mint_approval_token(requestor="u-rev", agent_id="02-pharmacovigilance",
                                      tool="safety.submit_report", args=args, approver="u-rev")
        assert False, "self-approval must be refused"
    except approvals.ApprovalInvalid:
        pass
    # bound approval (requestor != approver), approver commits -> allow
    bound = approvals.mint_approval_token(requestor="u-proc", agent_id="02-pharmacovigilance",
                                          tool="safety.submit_report", args=args, approver="u-rev")
    assert gw.invoke(user_claims=REV, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                     args=args, approval={"token": bound}).decision == "ALLOW"
    # replay of the single-use approval -> not allowed again
    assert gw.invoke(user_claims=REV, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                     args=args, approval={"token": bound}).decision != "ALLOW"
