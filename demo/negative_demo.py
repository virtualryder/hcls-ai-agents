#!/usr/bin/env python3
"""
HCLS Agent 02 (Pharmacovigilance) — NEGATIVE DEMO (the 10 things the platform refuses).

A CISO does not want to see the happy path; they want to see what is *denied*. This exercises
the SHIPPING controls (hcls_agent_platform.*) and proves each refusal fires. Nothing is mocked
except two deliberate fault injections (masker down, audit sink down) that prove fail-closed.

Run:  PYTHONPATH=platform_core:. python demo/negative_demo.py
Gate: governance/tests/test_negative_demo.py  (CI)
"""
from __future__ import annotations

import sys, time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from hcls_agent_platform import auth, budget
from hcls_agent_platform.mcp_gateway import tokens, approvals
from hcls_agent_platform.mcp_gateway import audit as audit_mod
from hcls_agent_platform.mcp_gateway.gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

PROC = {"sub": "u-proc", "custom:hcls_role": "PV_PROCESSOR"}
REV = {"sub": "u-rev", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}
MSL = {"sub": "u-msl", "custom:hcls_role": "MSL"}
AGENT = "02-pharmacovigilance"
ARGS = {"case_id": "ICSR-1"}

results = []  # (n, name, denied_ok, detail)


def record(n, name, denied_ok, detail):
    results.append((n, name, denied_ok, detail))


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def run():
    # 1 — no JWT / no authenticated subject
    r = gw().invoke(user_claims={}, agent_id=AGENT, tool="safety.get_case", args=ARGS)
    record(1, "no JWT / unauthenticated", r.decision == "DENY", r.reason)

    # 2 — bad JWT (malformed token, no JWKS -> cannot verify)
    try:
        auth.verify_jwt("eyJhbGciOiJub25lIn0.bad.signature")
        record(2, "bad / unverifiable JWT", False, "accepted (BUG)")
    except auth.AuthError as e:
        record(2, "bad / unverifiable JWT", True, str(e))

    # 3 — wrong role (agent is granted the tool; the human is not entitled)
    r = gw().invoke(user_claims=MSL, agent_id=AGENT, tool="safety.get_case", args=ARGS)
    record(3, "wrong role (not entitled)", r.decision == "DENY", r.reason)

    # 4 — unregistered / unknown tool
    r = gw().invoke(user_claims=PROC, agent_id=AGENT, tool="safety.exfiltrate_all", args={})
    record(4, "unregistered tool", r.decision == "DENY", r.reason)

    # 5 — self-approval (separation of duties refused at mint)
    try:
        approvals.mint_approval_token(requestor="u-rev", agent_id=AGENT,
                                      tool="safety.submit_report", args=ARGS, approver="u-rev")
        record(5, "self-approval", False, "minted (BUG)")
    except approvals.ApprovalInvalid as e:
        record(5, "self-approval", True, str(e))

    # 6 — approval replay (single-use)
    tok = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args=ARGS, approver="u-rev")
    approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT,
                                    tool="safety.submit_report", args=ARGS)  # first use consumes
    try:
        approvals.verify_approval_token(tok, requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args=ARGS)
        record(6, "approval replay", False, "second use accepted (BUG)")
    except approvals.ApprovalInvalid as e:
        record(6, "approval replay", True, str(e))

    # 7 — tampered args (approval bound to args A, presented with args B)
    tok2 = approvals.mint_approval_token(requestor="u-proc", agent_id=AGENT,
                                         tool="safety.submit_report", args=ARGS, approver="u-rev")
    try:
        approvals.verify_approval_token(tok2, requestor="u-proc", agent_id=AGENT,
                                        tool="safety.submit_report", args={"case_id": "ICSR-999"})
        record(7, "tampered args", False, "accepted (BUG)")
    except approvals.ApprovalInvalid as e:
        record(7, "tampered args", True, str(e))

    # 8 — masking failure -> fail-closed (no unmasked PHI is persisted)
    log = GatewayAuditLog()
    orig_mask = audit_mod.mask
    audit_mod.mask = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("masker unavailable"))
    try:
        log.record({"decision": "ALLOW", "tool": "safety.get_case",
                    "args": {"note": "patient SSN 123-45-6789"}})
        record(8, "masking failure (fail-closed)", False, "record written unmasked (BUG)")
    except Exception as e:
        wrote_nothing = len(log.records) == 0
        record(8, "masking failure (fail-closed)", wrote_nothing,
               f"raised {type(e).__name__}; no record persisted={wrote_nothing}")
    finally:
        audit_mod.mask = orig_mask

    # 9 — audit-sink failure -> fail-closed (no silent success without a trail)
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit sink down"))
    try:
        g.invoke(user_claims=PROC, agent_id=AGENT, tool="safety.get_case", args=ARGS)
        record(9, "audit-write failure (fail-closed)", False, "returned success with no audit (BUG)")
    except Exception as e:
        record(9, "audit-write failure (fail-closed)", True, f"raised {type(e).__name__} (no silent success)")

    # 10 — budget exceeded -> denied before spend (hard cap)
    meter = budget.BudgetMeter(agent_id=AGENT, dept="Pharmacovigilance",
                               monthly_token_cap=1000, cap_behavior="hard")
    meter.commit(900)
    d = meter.preflight(estimated_tokens=500)   # 900 + 500 > 1000
    record(10, "budget exceeded (pre-spend)", d.allowed is False, d.reason)


def main():
    print("=" * 70)
    print("  HCLS AGENT 02 — NEGATIVE DEMO (what the platform REFUSES)")
    print("=" * 70)
    run()
    ok = 0
    for n, name, denied, detail in results:
        tag = "DENIED ✓" if denied else "LEAKED ✗"
        ok += 1 if denied else 0
        print(f"  {n:>2}. [{tag}] {name:<34} {detail[:70]}")
    print("-" * 70)
    allpass = ok == len(results)
    print(f"  {ok}/{len(results)} refusals fired. "
          + ("ALL DENIES ENFORCED ✓" if allpass else "SOME CONTROL FAILED ✗"))
    print("=" * 70)
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(main())
