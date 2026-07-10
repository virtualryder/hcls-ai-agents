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
