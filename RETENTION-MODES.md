# S3 Object Lock — retention modes & governance-bypass controls

*The WORM evidence store (append-only audit + finalized regulated artifacts) is protected by S3 Object
Lock. Object Lock has two modes, and the difference is a real security control — not a detail. This is
operational guidance; reference accelerator, not legal advice (see `NOT-CLAIMS.md`).*

## The two modes

| Mode | Who can shorten/bypass retention | Use for |
|---|---|---|
| **COMPLIANCE** | **No one** — not IAM admins, not the account root. Retention cannot be shortened or the object deleted until it expires. | **Regulated production** (the default in these stacks). |
| **GOVERNANCE** | Only a principal with `s3:BypassGovernanceRetention` **and** the bypass header. | **Pilots / non-production**, where you may need to clean up test data. |

**Governance mode is bypassable** — AWS permits a user with `s3:BypassGovernanceRetention` to delete or
shorten a locked object. So a GOVERNANCE-mode bucket is only as strong as the IAM policy around that
permission. COMPLIANCE mode removes the bypass entirely.

## The controls this repo ships (in `infra/cloudformation/data.yaml`)

1. **Default `RetentionMode: COMPLIANCE`** — set `RetentionMode=GOVERNANCE` only for a pilot.
2. **Explicit deny on `s3:BypassGovernanceRetention`** (and `s3:DeleteObjectVersion`) for **everyone
   except an optional break-glass role** (`BreakGlassRoleArn`, empty by default = no bypass permitted).
   This makes the control explicit even in COMPLIANCE mode and is essential in GOVERNANCE mode.
3. **Deny insecure (non-TLS) transport** to the bucket.
4. **`DeletionPolicy: Retain` + `UpdateReplacePolicy: Retain`** so a stack delete never removes the evidence.
5. **Encryption at rest** (customer-managed KMS) and full public-access block.

## What the break-glass role must have (if you set one)

Per [`docs/KEY-MANAGEMENT.md`](docs/KEY-MANAGEMENT.md): MFA, a second approver, a hard time-box, and an
alarm on every use. A break-glass bypass is a declared incident, reviewed afterward. Prefer **no**
break-glass role in production (COMPLIANCE mode makes it moot).

## Enable logging of any attempt (do this at deploy)

- **CloudTrail S3 data events** on the WORM bucket — logs every `DeleteObject`, `PutObjectRetention`,
  and bypass attempt. (Data events are account-level; enable them on the trail that covers this account.)
- **IAM Access Analyzer** — prove no external principal and no unintended `BypassGovernanceRetention`
  grant. Captured at deploy via `tools/collect_runtime_evidence.sh` (see `RUNTIME-EVIDENCE-RUNBOOK.md`).

## Proven offline

- The audit layer is append-only and the IaC carries the mutation/bypass denies + Object Lock —
  `governance/tests/test_evidence_vault.py` (append-only + IaC deny/Object-Lock + `BypassGovernanceRetention` deny).
- The runtime **overwrite-denied** proof (an actual `AccessDenied` on a locked object) is captured at
  deploy by the WORM probe in `tools/collect_runtime_evidence.sh`.

**Recommendation:** GOVERNANCE for pilots (with the bypass-deny + break-glass discipline above),
**COMPLIANCE for regulated production.**
