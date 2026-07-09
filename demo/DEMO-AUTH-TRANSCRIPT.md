# Aegis MCP gateway — end-to-end authorization walkthrough (recorded transcript)

**Self-service artifact.** This is the actual captured output of `demo/demo_auth.py`. It answers
the question every CISO and security architect asks about an agent platform: **"show me the auth —
how does a request actually get authorized, and what stops an agent (or a compromised one) from
doing more than it should?"** Every line below comes from the *shipping* gateway modules
(`hcls_agent_platform.auth`, `.mcp_gateway.{policy,tokens,approvals,gateway,audit}`) — nothing is
mocked. The companion `demo_openfda.py` proves the pattern against a real system of record; this
proves the authorization chain itself.

> Reference accelerator — not an AWS service, not a compliance certification. In production the dev
> HMAC token signer is replaced by **Amazon Bedrock AgentCore Identity / Amazon Cognito + STS**, OIDC
> verification uses the customer IdP's **JWKS**, single-use approvals use an atomic **DynamoDB** claim,
> and the audit sink is append-only (**QLDB / S3 Object Lock**). Decision, intersection, token,
> approval, and audit semantics are identical. See `demo/demo-auth-walkthrough.html` for the visual version.

---

## The chain, in one line

`IdP federation → token exchange → least-privilege intersection → human-authority commit (separation of duties) → append-only audit`, deny-by-default at every hop.

## Recorded run (`PYTHONPATH=platform_core:. python demo/demo_auth.py`)

```
======================================================================
  AEGIS MCP GATEWAY — END-TO-END AUTHORIZATION WALKTHROUGH
======================================================================

1 / 5  IdP FEDERATION  (OIDC identity -> verified, role-bearing claims)
  id_token (RS256, truncated): eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
  federation: [real] RS256 ID token minted + verified offline (sig+aud+exp)
  subject=u-pat-001  groups=['GRP-PV-PROCESSORS']
  -> mapped app role(s): ['PV_PROCESSOR']
  ... (reviewer -> PV_MEDICAL_REVIEWER, MSL -> MSL) ...

2 / 5  TOKEN EXCHANGE  (verified identity -> short-lived, tool-scoped token)
  minted: jti=ed6c912b  scope=['safety.get_case']  ttl=60s  (no standing service account)
  deny paths on the token itself:
    [DENY] confused-deputy (token for tool A replayed at tool B): token tool scope mismatch
    [DENY] expired token: token expired
    [DENY] tampered signature: bad token signature

3 / 5  LEAST-PRIVILEGE INTERSECTION   permitted ⇔ tool ∈ agent_grant ∩ user_entitlement
  same tool (safety.get_case), three identities:
  [ALLOW] safety.get_case      processor via PV agent
  [DENY ] safety.get_case      acting user (roles=['MSL']) is not entitled to 'safety.get_case'
                               (an agent may never exceed the user's own permissions)
  [DENY ] safety.get_case      agent '07-rwe-heor' is not granted 'safety.get_case' (over-reach denied)

4 / 5  HUMAN-AUTHORITY COMMIT + SEPARATION OF DUTIES   (safety.submit_report — irreversible)
  [PEND ] safety.submit_report   human approval required
  [DENY]  self-approval refused at mint: self-approval is forbidden (separation of duties)
  [ALLOW] safety.submit_report   bound approval, approver commits (SoD satisfied)
  [DENY]  safety.submit_report   replay rejected: approval token already used (replay) -> commit withheld

5 / 5  APPEND-ONLY AUDIT   (every decision recorded, PHI-masked, with lineage)
  6 records: ALLOW=2, DENY=2, PENDING_APPROVAL=2
    ALLOW            safety.get_case        user=u-pat-001
    DENY             safety.get_case        user=u-sam-003
    DENY             safety.get_case        user=u-mona-002
    PENDING_APPROVAL safety.submit_report   user=u-mona-002
    ALLOW            safety.submit_report   user=u-mona-002   approved_by=u-mona-002
    PENDING_APPROVAL safety.submit_report   user=u-mona-002
```

## What each beat proves to a reviewer

| Beat | Reviewer question it answers | Mechanism (shipping code) |
|---|---|---|
| 1 · IdP federation | Where do identities and roles come from? | OIDC verified fail-closed (`auth.verify_jwt`); IdP groups mapped to app roles — the platform manages **no** user accounts |
| 2 · Token exchange | What does the agent actually carry to the system of record? | A token scoped to **one** tool, ~60s TTL, no standing service account (`tokens.mint_scoped_token`); confused-deputy / expiry / tamper all rejected |
| 3 · Intersection | Can an agent do more than the human it acts for? | **No.** `permitted ⇔ tool ∈ agent_grant ∩ user_entitlement` — same tool ALLOWs for the processor, DENYs for an unentitled human, DENYs for an over-reaching agent |
| 4 · Human commit + SoD | Who can perform the irreversible act? | The commit is withheld from **every** agent grant; it needs a bound, single-use, separation-of-duties human approval — self-approval and replay are refused (`approvals.py`) |
| 5 · Audit | How do you prove any of this later? | Every ALLOW/DENY/PENDING is on an append-only, PHI-masked trail with lineage and the approver identity (`audit.py`) |

## Reproduce it yourself

```bash
cd hcls-ai-agents
PYTHONPATH=platform_core:. python demo/demo_auth.py          # the walkthrough
PYTHONPATH=platform_core:. pytest governance/tests/test_auth_walkthrough.py -q   # the CI gate
```

The RS256 ID-token step is real crypto when `PyJWT` + `cryptography` are installed (offline, no
JWKS URL needed); otherwise it uses the dev pre-verified-claims path the gateway already supports.
Either way the run is deterministic and needs no network or API key.

**Pointers:** policy (intersection) `platform_core/hcls_agent_platform/mcp_gateway/policy.py` ·
tokens `.../mcp_gateway/tokens.py` · bound approvals `.../mcp_gateway/approvals.py` ·
gateway `.../mcp_gateway/gateway.py` · IdP federation `.../auth.py`.
