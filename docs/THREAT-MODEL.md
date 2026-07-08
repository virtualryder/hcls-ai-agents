# Threat Model — HCLS AI Agent Suite

> **Purpose.** Give a CISO / security architect a complete, named view of the threats an agentic,
> PHI-touching, GxP-regulated AI workflow faces — and the specific control that mitigates each, with a
> file path. Scoped to the reference control plane + IaC; the customer owns IdP, live connectors, and
> the validated production surface (see `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`).

## System & trust boundaries
```
[Human staff] → IdP (Okta/Entra/Ping) → CloudFront+WAF → Cognito(JWT) → Agent (Fargate/AgentCore)
      │                                                                      │
      │                                                            MCP AUTHORIZATION GATEWAY  ← trust boundary
      │                                                                      │
      └──── (approval) ── Reviewer ──────────────────────────────  Connectors → Veeva/Argus/Medidata/QMS/MES/LIMS
                                                                     Bedrock (in-VPC) + Guardrails
                                                                     DynamoDB audit (append-only) + S3 WORM
```
**Key boundary:** the **MCP gateway**. Nothing reaches a system of record or the model except through it.
Authorization, masking, approval, token minting, and audit all happen at this single enforcement point —
**outside the model**, so a prompt cannot disable them.

## Assets to protect
PHI / patient data · regulated artifacts (ICSR, submission sections, CAPA records, batch dispositions) ·
the audit trail (legal evidence) · system-of-record credentials · model/prompt integrity.

## STRIDE threats → mitigations (with file paths)

| # | Threat (STRIDE) | Scenario | Mitigation | Where |
|---|---|---|---|---|
| T1 | **Spoofing** | Caller forges identity / roles to act as a clinician | RS256/JWKS JWT verification; client-supplied roles untrusted; fail-closed on missing subject | `auth.py`, `mcp_gateway/gateway.py` (step 1) |
| T2 | **Tampering (prompt injection)** | Malicious content in a source record tells the agent to exfiltrate or over-act | Controls live in the gateway, **not** the model; deny-by-default authorization; Bedrock Guardrails; red-team test proves bypass is denied | `mcp_gateway/policy.py`, `governance/redteam/` |
| T3 | **Repudiation** | A party denies an action / the audit is altered | Append-only DynamoDB + S3 Object Lock (WORM); every attempt logged with actor, ts, sources, model+prompt version | `mcp_gateway/audit*.py`, `infra/cloudformation/data.yaml` |
| T4 | **Information disclosure (PHI egress)** | Patient data leaks to the model, logs, or a third party | PHI masking **before** any model/audit write; Bedrock via VPC endpoint (PrivateLink); Guardrails PII filters; no data egress to external AI APIs | `phi.py`, `llm_factory.py`, `security.yaml` |
| T5 | **Denial of service / cost** | Flood of requests drives Bedrock spend | WAF rate limiting (edge); per-tool scoped tokens; Budgets + Cost Anomaly Detection (customer) | `infra/cloudformation/edge.yaml`, `AWS-ACCOUNT-PREREQUISITES.md` |
| T6 | **Elevation of privilege (agent over-reach)** | The agent performs an action beyond the human it acts for | Least-privilege **intersection** (agent grant ∩ user entitlement); an agent can never exceed the user | `mcp_gateway/policy.py::decide` |
| T7 | **Unauthorized irreversible commit** | The agent (or a mis-scoped human) commits a regulated act (submit ICSR / close CAPA / release batch) | Consequential commits **withheld from every agent grant** (`CONSEQUENTIAL_COMMITS`); only a bound human reviewer may commit; enforced by test | `policy.py`, `tests/test_mcp_gateway.py::test_consequential_actions_withheld_from_agents` |
| T8 | **Approval forgery / replay / self-approval** | A reviewer token is forged, reused, retargeted, or self-issued | Bound approval tokens: HMAC-signed, single-use (jti), args-bound (tamper-evident), separation-of-duties (approver ≠ requestor); `STRICT_APPROVAL=1` rejects unbound dicts | `mcp_gateway/approvals.py` |
| T9 | **Hallucination / data-integrity defect** | The model invents a number/entity in a regulated artifact | Grounding verification: every figure/entity must trace to source or fail closed; outputs cite sources | `governance/grounding.py`, per-agent `quality_checker.py` |
| T10 | **Model / prompt drift** | A silent prompt change alters a regulated output | Prompts hash-pinned in a manifest; CI fails on un-bumped drift (model-risk change control) | `governance/prompt_registry.py`, `prompt_manifest.json` |
| T11 | **Standing credentials / lateral movement** | A long-lived service account is stolen | No standing service accounts; per-call short-lived scoped tokens; Secrets Manager + KMS | `mcp_gateway/tokens.py`, `security.yaml` |
| T12 | **Supply chain** | A poisoned dependency enters the build | Pinned deps; deps vendored into Lambda zips deterministically; CI byte-compile + tests gate every change | `scripts/build_lambdas.sh`, `.github/workflows/ci.yml` |
| T13 | **Connector blast radius** | A compromised connector reads beyond its remit | One validated connector per system of record; tool names map 1:1 to gateway targets; de-identification enforced at the gateway for RWD (Agents 04/07) | `connectors/`, `policy.py` |
| T14 | **Fairness / disparate impact** | A flag/rank workflow produces biased cohorts | Representativeness / four-fifths fairness screen; human review on any consequential flag | `governance/fairness/` |

## Residual risks (deployer-owned)
Live-connector validation, CSV/CSA, IdP entitlement correctness, penetration testing, KMS key custody,
and production retention/DR are the customer's responsibility — tracked in
`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` and the CIO deck's shortfalls/backlog slides.
