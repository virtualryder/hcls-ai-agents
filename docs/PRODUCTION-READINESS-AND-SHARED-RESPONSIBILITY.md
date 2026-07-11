# Production Readiness & Shared Responsibility — HCLS AI Agent Suite

> What is **reference-implemented** in this repo vs. what the **customer/SI must complete** to run in
> production with PHI under a BAA and (where applicable) GxP / 21 CFR Part 11. Read alongside
> `SHARED-RESPONSIBILITY-MATRIX.md` (AWS vs. SI vs. sponsor) and the CIO deck's shortfalls/backlog slides.

## Maturity, restated for security reviewers
The suite is **Demonstrated + Deployable-by-design**: the control plane runs, 580 tests pass with no API
key, and the IaC validates. It is **not** CSV/CSA-validated, SOC 2 / HITRUST-certified, or penetration-tested.
Production-readiness is the engagement.

## What's reference-implemented (in this repo)
- Deny-by-default authorization, least-privilege intersection, **consequential commits withheld from agents**.
- Bound human-approval tokens (single-use, separation-of-duties, args-bound); `STRICT_APPROVAL` for prod.
- PHI masking before model/audit; private-connectivity Bedrock + Guardrails; grounding verification; prompt hash-pinning.
- Append-only audit + S3 Object Lock (WORM); scoped short-lived tokens; KMS CMK per data class.
- CloudFormation (network, edge, security, data, connectors, dual gateway, agent) + per-agent SAM golden paths + Terraform.
- 580 automated tests (incl. governance + red-team + the withholding test), run in one command via `make test`.

## What the customer/SI must complete (production gate)
| Area | Owner | Gate |
|---|---|---|
| **Computer-system validation (CSV/CSA)** — IQ/OQ/PQ + traceability | Sponsor QA | Required before any GxP go-live |
| **IdP federation + entitlement source of truth** | Customer | Reviewer roles map to `custom:hcls_role`; a non-approver is correctly denied |
| **Live connectors** (Veeva/Argus/Medidata/QMS/MES/LIMS) | SI | Validated against the real system; a read + a test write appear in the audit |
| **Penetration test** of the deployed surface | Customer/3rd party | Production-readiness gate |
| **Bedrock cost & clinical-accuracy validation** | Sponsor | Against the customer's own data |
| **Continuous monitoring + alarms** | Customer ops | CloudWatch alarms on the IR signals (see IR doc) |
| **BAA, data residency, retention/DR** | Customer | Region + retention per policy; WORM retention set |
| **SOC 2 / HITRUST** (if required) | Customer program | Out of scope for the accelerator |

## The honest "set `STRICT_APPROVAL=1`" note
In dev/demo the gateway accepts the legacy reviewer dict so the suite runs with no key. **In production set
`STRICT_APPROVAL=1`** so only a *bound* approval token (single-use, SoD, args-bound) satisfies the human
gate — and confirm a replayed/tampered/self-approval is rejected (covered by `approvals` tests).

## Go-live checklist
See `docs/DEPLOY-QUICKSTART.md` §8 — every box (Guardrail tested, IdP denies a non-approver, live connector
read+write audited, HITL pause verified, audit append-only proven, prompt manifest matches, `Environment=prod`
forces the Guardrail, WAF enabled) must be checked before promotion.
