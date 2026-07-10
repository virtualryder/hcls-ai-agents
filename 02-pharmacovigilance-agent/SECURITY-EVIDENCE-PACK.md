# Security Evidence Pack — HCLS Agent 02 — Pharmacovigilance ICSR Intake

*The security-review companion to [`ASSURANCE-PACKET.md`](ASSURANCE-PACKET.md). It adds the IAM role
matrix and the MCP authorization matrix (both buildable now), and lists the **runtime** proofs that are
captured at deploy time. Nothing here is asserted before it is captured — see the status column.*

> Reference accelerator — not an AWS service, not a certification. See [`../NOT-CLAIMS.md`](../NOT-CLAIMS.md).

## 1. MCP authorization matrix (what this agent can and cannot do)

Effective permission = **agent grant ∩ user entitlement** (role: `PV_PROCESSOR`). Consequential acts are
withheld from the agent in code and require a different, entitled human role + a bound approval.
Source: the pack's `mcp_gateway/policy.py`. Proven by the negative demo (#3–#7) and the withholding test.

| Tool | Agent authority | Access / who commits |
|---|---|---|
| `safety.get_case` | granted | read |
| `safety.search_duplicates` | granted | read |
| `safety.write_case_draft` | granted | write · human approval |
| `meddra.code_term` | granted | read |
| `whodrug.code_drug` | granted | read |
| `safety.submit_report` | **withheld from the agent** | PV_MEDICAL_REVIEWER + bound approval (ICSR submission) |

Every high-risk (write) tool additionally requires a **bound, single-use, separation-of-duties**
approval before execution (`STRICT_APPROVAL=1` in production).


## 1a. MCP authorization negative-test matrix (12 cases — proven, CI-gated)

The full checklist a security reviewer expects, proven against the **shipping gateway** by
`governance/tests/test_mcp_authz_matrix.py` (**12/12**). Framing maps to the deployed edge (401/403/deny);
offline the gateway returns a DENY decision or the primitive raises. This is the "hard proof per repo"
— the same 12 cases pass identically for every hero.

| # | Attempt | Edge | Proven by |
|---|---|---|---|
| 1 | No token / unauthenticated | **401** | gateway → DENY (no authenticated subject) |
| 2 | Bad / unverifiable token | **401** | JWT verification raises (RS256/JWKS; `none`/HS rejected) |
| 3 | Valid token, **missing scope** | **403** | a scoped token minted for tool A is rejected at tool B |
| 4 | Unregistered tool | deny | unknown-tool deny (allow-list) |
| 5 | Wrong role (not entitled) | deny | least-privilege intersection deny |
| 6 | Wrong data class | deny | data-class boundary enforced via tool entitlement (an out-of-domain tool is denied) |
| 7 | Self-approval | deny | approver == requester refused at mint (SoD) |
| 8 | Replayed approval | deny | single-use nonce / jti consumed |
| 9 | Tampered approval args | deny | args / binding hash mismatch |
| 10 | Stale / expired approval | deny | approval `exp` in the past is rejected |
| 11 | No outbound credential | deny | no valid scoped token → the connector is unreachable (prod outbound-auth: IAM / OAuth / token-exchange / on-behalf-of) |
| 12 | Audit write failure | deny | fail-closed — no silent success without an audit trail |

```bash
PYTHONPATH=platform_core:. pytest governance/tests/test_mcp_authz_matrix.py -q   # 12 passed
```

The literal HTTP **401/403** status codes at the deployed **API Gateway / AgentCore Gateway** edge
(and the outbound-auth denial to the system of record) are captured at deploy time — see the runtime
slots in §3 and [`../RUNTIME-EVIDENCE-RUNBOOK.md`](../RUNTIME-EVIDENCE-RUNBOOK.md). AWS AgentCore note:
`AUTHENTICATE_ONLY` does not enforce authorization and "No Authorization" is not for production — this
gateway always authorizes (deny-by-default) and mints a scoped outbound credential per call.

## 2. IAM role matrix (least privilege, per role)

The golden path provisions one **scoped role per function** — no shared broad role. Exact ARNs +
policies are captured at deploy via IAM Access Analyzer (see §3); the pattern:

| Role | Scope (least privilege) | Notable denies |
|---|---|---|
| Agent/orchestration execution role | invoke the workflow + the connector Lambda; write audit via the gateway | no direct system-of-record access; assume limited to the workflow service principals |
| Connector Lambda role | call the one system-of-record endpoint for its `connector_kind`; read its secret | scoped to that connector only |
| Audit-writer role | `dynamodb:PutItem` on the audit table only | **explicit Deny on `UpdateItem` / `DeleteItem`** (append-only) |
| WORM evidence role | `s3:PutObject` to the Object-Lock bucket | no `DeleteObject` / no lock-config change |
| Reviewer service role | mint bound approvals; resume the Step Functions execution | cannot invoke tools directly |
| KMS usage | encrypt/decrypt scoped to the data-class CMK | key policy separates admin from usage (SoD) |

Data class for this hero: **PHI (HealthLake variant); openFDA reference path is public/de-identified**.

## 3. Runtime proofs — captured at clean-account deploy

These are produced by `tools/collect_runtime_evidence.sh` against a deployed stack (see
[`../RUNTIME-EVIDENCE-RUNBOOK.md`](../RUNTIME-EVIDENCE-RUNBOOK.md)) — **not** asserted here until captured.

| Proof | Status | Capture |
|---|---|---|
| Runtime PHI/PII/CJI masking (real audit record) | ☐ pending clean-account capture | `--audit-table` scan |
| Bedrock Guardrails blocking a real invoke | ☐ pending | guardrail config + blocked-invoke screenshot |
| Locked egress (NFW allow + drop) | ☐ pending | `--log-group` NFW alert logs |
| IAM Access Analyzer findings | ☐ pending | `accessanalyzer list-findings` |
| CloudWatch security alarms + dashboard | ☐ pending | `describe-alarms` + dashboard export |
| WORM overwrite denied (Object Lock) | ☐ pending | `--audit-bucket` overwrite probe |
| Step Functions paused at the human gate | ☐ pending | execution screenshot |
| Teardown — zero residual resources | ☐ pending | `destroy.sh` output |

## 4. Already proven offline (cite now — no deploy needed)

- **10-point negative demo** (`make neg-demo`): no/bad JWT, wrong role, unregistered tool, self-approval,
  replay, tampered args, masking fail-closed, audit-write fail-closed, budget exceeded — **10/10 enforced**, CI-gated.
- **Evidence Vault** (`test_evidence_vault.py`): audit append-only by API; IaC denies `UpdateItem`/`DeleteItem` + S3 Object Lock.
- **End-to-end auth chain** (`make auth-demo`): IdP → token exchange → intersection → SoD → append-only audit.
- **Scored quality** (`make eval-*`): thresholds incl. **PHI-leak = 0**.
- **AGP v1.0 conformance** ([`../AGP-CONFORMANCE.md`](../AGP-CONFORMANCE.md)) + **security CI** ([`../SECURITY-CI.md`](../SECURITY-CI.md)).

*If any statement reads stronger than [`../NOT-CLAIMS.md`](../NOT-CLAIMS.md) or
[`../MATURITY.yaml`](../MATURITY.yaml), those files govern.*
