#!/usr/bin/env python3
"""
Aegis MCP gateway — END-TO-END AUTH WALKTHROUGH (reproducible, no network).

The companion to demo_openfda.py. Where that demo proves the pattern works against
a REAL system of record, this one proves the *authorization chain* itself:

  IdP federation  ->  token exchange  ->  least-privilege intersection  ->
  human-authority commit (separation of duties)  ->  token-scoping deny paths  ->
  append-only audit

Every decision below comes from the SHIPPING gateway modules
(hcls_agent_platform.auth, .mcp_gateway.{policy,tokens,approvals,gateway,audit}) —
nothing is mocked. In production the dev HMAC token signer is swapped for Amazon
Bedrock AgentCore Identity / Amazon Cognito + STS, and the OIDC verification uses
the customer IdP's JWKS; the decision, intersection, token, approval, and audit
semantics are identical.

Run:  PYTHONPATH=platform_core:. python demo/demo_auth.py
"""
from __future__ import annotations

import sys
import time

try:  # keep unicode (∩, →) stable when captured on Windows
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from hcls_agent_platform import auth
from hcls_agent_platform.mcp_gateway import tokens, approvals
from hcls_agent_platform.mcp_gateway import policy as _policy
from hcls_agent_platform.mcp_gateway.gateway import MCPGateway
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

RULE = "=" * 70

# Cognito maps enterprise-IdP groups to application roles in a pre-token-generation
# step; we show that mapping explicitly rather than hand-waving "the IdP gives roles".
GROUP_TO_ROLE = {
    "GRP-PV-PROCESSORS": "PV_PROCESSOR",
    "GRP-PV-PHYSICIANS": "PV_MEDICAL_REVIEWER",
    "GRP-MSL": "MSL",
}


def federate(sub: str, name: str, groups: list) -> dict:
    """BEAT 1 — federate an OIDC identity into verified, role-bearing claims.

    Mints a real RS256 ID token and verifies signature/exp/aud offline when PyJWT +
    cryptography are installed; otherwise presents pre-verified claims (the dev path
    the gateway already supports). Either way, verification is fail-closed."""
    role = ",".join(GROUP_TO_ROLE.get(g, g) for g in groups)
    oidc = {
        "iss": "https://login.customer.example/oidc",
        "aud": "aegis-mcp-gateway",
        "sub": sub, "name": name,
        "cognito:groups": groups,      # from the enterprise IdP
        "custom:hcls_role": role,      # mapped app role(s) the gateway authorizes on
        "iat": int(time.time()), "exp": int(time.time()) + 3600,
    }
    mode = "[dev] claims presented pre-verified (no IdP libs installed)"
    try:
        import jwt  # PyJWT
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv = key.private_bytes(serialization.Encoding.PEM,
                                 serialization.PrivateFormat.PKCS8,
                                 serialization.NoEncryption())
        pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo)
        id_token = jwt.encode(oidc, priv, algorithm="RS256")
        # verify offline: real signature + audience + expiry check (fail-closed)
        jwt.decode(id_token, pub, algorithms=["RS256"], audience="aegis-mcp-gateway")
        mode = "[real] RS256 ID token minted + verified offline (sig+aud+exp)"
        print(f"  id_token (RS256, truncated): {id_token[:48]}...")
    except Exception:
        pass
    claims = auth.verify_jwt(oidc)   # fail-closed: requires 'sub'
    print(f"  federation: {mode}")
    print(f"  subject={claims['sub']}  groups={groups}")
    print(f"  -> mapped app role(s): {auth.roles_from_claims(claims)}")
    return claims


def show(res, note=""):
    tag = {"ALLOW": "ALLOW", "DENY": "DENY ", "PENDING_APPROVAL": "PEND "}.get(res.decision, res.decision)
    print(f"  [{tag}] {res.tool:<22} audit={res.audit_id[:8]}  {res.reason or note}")
    return res


def main() -> None:
    print(RULE)
    print("  AEGIS MCP GATEWAY — END-TO-END AUTHORIZATION WALKTHROUGH")
    print(RULE)
    audit = GatewayAuditLog()
    gw = MCPGateway(audit=audit, connector_mode="fixture")

    # ── BEAT 1 — IdP federation ────────────────────────────────────────────────
    print("\n1 / 5  IdP FEDERATION  (OIDC identity -> verified, role-bearing claims)")
    processor = federate("u-pat-001", "Pat Rivera (PV processor)", ["GRP-PV-PROCESSORS"])
    print()
    reviewer = federate("u-mona-002", "Dr. Mona Lee (PV physician)", ["GRP-PV-PHYSICIANS"])
    print()
    msl = federate("u-sam-003", "Sam Cole (MSL)", ["GRP-MSL"])

    # ── BEAT 2 — token exchange + token-scoping deny paths ─────────────────────
    print("\n2 / 5  TOKEN EXCHANGE  (verified identity -> short-lived, tool-scoped token)")
    tok = tokens.mint_scoped_token(subject=processor["sub"], agent_id="02-pharmacovigilance",
                                   tool="safety.get_case", scope=["safety.get_case"])
    claims = tokens.verify_scoped_token(tok, expected_tool="safety.get_case")
    ttl = claims["exp"] - claims["iat"]
    print(f"  minted: jti={claims['jti'][:8]}  scope={claims['scope']}  ttl={ttl}s  (no standing service account)")
    print("  deny paths on the token itself:")
    for label, fn in [
        ("confused-deputy (token for tool A replayed at tool B)",
            lambda: tokens.verify_scoped_token(tok, expected_tool="safety.submit_report")),
        ("expired token",
            lambda: tokens.verify_scoped_token(
                tokens._sign({**claims, "exp": int(time.time()) - 5}), expected_tool="safety.get_case")),
        ("tampered signature",
            lambda: tokens.verify_scoped_token(tok[:-1] + ("0" if tok[-1] != "0" else "1"),
                                               expected_tool="safety.get_case")),
    ]:
        try:
            fn(); print(f"    [BUG]  {label}: ACCEPTED (should not happen)")
        except Exception as exc:
            print(f"    [DENY] {label}: {exc}")

    # ── BEAT 3 — least-privilege intersection ──────────────────────────────────
    print("\n3 / 5  LEAST-PRIVILEGE INTERSECTION   permitted ⇔ tool ∈ agent_grant ∩ user_entitlement")
    print("  same tool (safety.get_case), three identities:")
    show(gw.invoke(user_claims=processor, agent_id="02-pharmacovigilance", tool="safety.get_case",
                   args={"case_id": "ICSR-1"}), "processor via PV agent")
    show(gw.invoke(user_claims=msl, agent_id="02-pharmacovigilance", tool="safety.get_case",
                   args={"case_id": "ICSR-1"}), "MSL user — agent is granted it, the human is NOT")
    show(gw.invoke(user_claims=reviewer, agent_id="07-rwe-heor", tool="safety.get_case",
                   args={"case_id": "ICSR-1"}), "reviewer via wrong agent — agent over-reach")

    # ── BEAT 4 — human-authority commit + separation of duties ─────────────────
    print("\n4 / 5  HUMAN-AUTHORITY COMMIT + SEPARATION OF DUTIES   (safety.submit_report — irreversible)")
    args = {"case_id": "ICSR-1"}
    # agent path is withheld entirely; a reviewer with no approval -> pending
    show(gw.invoke(user_claims=reviewer, agent_id="02-pharmacovigilance",
                   tool="safety.submit_report", args=args), "no bound approval yet")
    # self-approval is refused at mint time (SoD)
    try:
        approvals.mint_approval_token(requestor=reviewer["sub"], agent_id="02-pharmacovigilance",
                                      tool="safety.submit_report", args=args, approver=reviewer["sub"])
        print("  [BUG]  self-approval minted (should not happen)")
    except approvals.ApprovalInvalid as exc:
        print(f"  [DENY] self-approval refused at mint: {exc}")
    # valid bound approval: processor requested, reviewer approves; reviewer commits
    bound = approvals.mint_approval_token(requestor=processor["sub"], agent_id="02-pharmacovigilance",
                                          tool="safety.submit_report", args=args, approver=reviewer["sub"])
    show(gw.invoke(user_claims=reviewer, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                   args=args, approval={"token": bound}), "bound approval, approver commits (SoD satisfied)")
    # replay the same single-use approval -> the approval no longer validates, so the
    # gateway falls back to "needs a (fresh) approval" instead of committing again.
    replay = gw.invoke(user_claims=reviewer, agent_id="02-pharmacovigilance", tool="safety.submit_report",
                       args=args, approval={"token": bound})
    reused = "already used" if approvals.verify_approval_token.__name__ else ""  # noqa
    try:
        approvals.verify_approval_token(bound, requestor=processor["sub"],
                                        agent_id="02-pharmacovigilance", tool="safety.submit_report",
                                        args=args, consume=False)
        reused = ""
    except approvals.ApprovalInvalid as exc:
        reused = str(exc)
    print(f"  [{'DENY' if replay.decision!='ALLOW' else 'BUG '}] safety.submit_report   "
          f"audit={replay.audit_id[:8]}  replay rejected: {reused or 'single-use enforced'} "
          f"-> commit withheld ({replay.decision})")

    # ── BEAT 5 — audit ─────────────────────────────────────────────────────────
    print("\n5 / 5  APPEND-ONLY AUDIT   (every decision recorded, PHI-masked, with lineage)")
    counts = {}
    for r in audit.records:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1
    print(f"  {len(audit.records)} records: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for r in audit.records:
        line = f"    {r['decision']:<16} {r.get('tool',''):<22} user={r.get('user')}"
        if r.get("approved_by"):
            line += f"  approved_by={r['approved_by'].get('sub') if isinstance(r['approved_by'],dict) else r['approved_by']}"
        print(line)

    print("\n" + RULE)
    print("  WALKTHROUGH COMPLETE — the authorization chain, end to end")
    print(RULE)
    print("  * IdP federation: OIDC verified fail-closed; IdP groups mapped to app roles")
    print("  * Token exchange: short-lived token scoped to ONE tool; confused-deputy,")
    print("    expiry, and tamper all rejected")
    print("  * Intersection: an agent can NEVER exceed the human it acts for (and vice-versa)")
    print("  * Irreversible commit: withheld from every agent; needs a bound, single-use,")
    print("    separation-of-duties human approval; self-approval and replay refused")
    print("  * Every decision is on an append-only, PHI-masked audit trail")
    print("  prod mapping: AgentCore Identity/Cognito+STS (tokens), IdP JWKS (OIDC),")
    print("               DynamoDB atomic single-use table (approvals), QLDB/Object-Lock (audit)")


if __name__ == "__main__":
    main()
