# External Review — Validation & Remediation Plan

**Source:** independent static review (ChatGPT), scoring the repo **58/100** — "strong accelerator; not production-ready."
**This document:** validates each finding against the *actual code* (not the review's prose), assigns a verdict, and
defines the fix, the acceptance test, and the owner. **Code line references are from commit at time of writing.**

> **Bottom line up front.** The review is substantially **correct on the deployed/AWS-native path**. The strongest
> governance logic lives in `platform_core/` and is unit-tested there — but several of those controls (bound approval
> verification, fail-closed audit, identity trust, the data contract between the HITL gate and the finalizer) are **not
> carried through into the AWS-native Lambda/Step Functions path that an SA would actually deploy**. That gap between
> "tested in `platform_core`" and "enforced in the deployed artifact" is the real issue, and it is fixable.

---

## How to read the verdict column

| Verdict | Meaning |
|---|---|
| ✅ **Confirmed** | Reproduced in the code exactly as described. |
| ◑ **Partially confirmed** | Real, but narrower or already partly mitigated (noted per row). |
| ◐ **Confirmed, with nuance** | Real on the deployed path, but the correct primitive already exists elsewhere and only needs to be wired through. |
| ✖ **Refuted / outdated** | Not true against current code. |

---

## P0 — must fix before *any* customer deployment

| # | Finding | Verdict | Evidence (file) | Fix | Acceptance test |
|---|---|---|---|---|---|
| F1 | Native finalize completes via a **stub**, not the governed connector; smoke test only asserts `SUCCEEDED` | ✅ Confirmed | `aws-native-reference/02-pharmacovigilance/lambdas/finalize.py` `_submit_report()` returns a generated id; `smoke_test.sh` asserts terminal state only | Replace stub with governed connector call; smoke test must assert `case_status==SUBMITTED` **and** an immutable audit row exists | New `test_finalize_submits_via_connector`; smoke test greps for `SUBMITTED` + audit row |
| F2 | Human approval **not cryptographically/operationally enforced** in the deployed path (finalize trusts a bare `approved` bool) | ◐ Confirmed, with nuance | `finalize.py`: `approved = bool(review.get("approved"))`. The real primitive **exists** in `platform_core/.../mcp_gateway/approvals.py` (HMAC, SoD, args-bound, single-use) but finalize never calls it | Finalize verifies a **bound approval token** (reviewer identity, role, requester≠approver, expiry, exact args hash, single-use) before the connector call | `test_finalize_rejects_unbound_approval`, `…_rejects_self_approval`, `…_rejects_tampered_args`, `…_rejects_replay` |
| F3 | Connector reads **request-body-supplied identity before** the authenticated authorizer context | ✅ Confirmed | `_shared/connector/handler.py` `_claims()` returns `event["identity"/"claims"/"userClaims"]` **before** `requestContext.authorizer.jwt.claims` | Prefer authorizer/JWT claims; only honor body identity when `HCLS_LOCAL_TEST=1`; never in a network-originated request | `test_claims_prefers_authorizer_over_body`, `test_body_identity_ignored_without_local_flag` |
| F4 | Review/approval **key-schema mismatch**: table keyed `request_id` (native) / `approval_id` (golden-path), but `hitl_notify` writes `case_id` | ✅ Confirmed | `data.yaml` HASH `request_id`; golden-path HASH `approval_id`; `hitl_notify.py` `Item={"case_id":…}` (write fails, is caught, continues) | Standardize on **`approval_id`** across table, `hitl_notify`, ASL `$.review`, and finalize lookup | `test_hitl_notify_writes_approval_id_key`; ASL contract test |
| F4b | ASL routes reviewer result to `$.review` (sibling of `$.body`) but finalize reads `review` **inside** the case body → an approved callback reads as **unapproved** | ✅ Confirmed | `pharmacovigilance.asl.json` HITL `ResultPath:"$.review"`, Finalize params `{body.$:"$.body", review.$:"$.review"}`; `finalize.py` reads `case_state.get("review")` | Finalize must read `event["review"]` (the sibling); add a contract test binding ASL output shape to finalize input | `test_finalize_reads_review_from_event_sibling` |
| F5 | Audit trail is **neither append-only nor fail-closed**: role grants `UpdateItem`/`BatchWriteItem`; writes are best-effort and swallow exceptions; only a summary is persisted | ✅ Confirmed | `security.yaml` grants `dynamodb:UpdateItem`,`BatchWriteItem`; `connector/handler.py` `_audit_to_dynamo` is "best-effort", try/except pass | Conditional `PutItem` (`attribute_not_exists`) for immutability; drop `UpdateItem`/`DeleteItem`/`BatchWriteItem` on the audit table; persist full evidence; failure blocks or quarantines the action | `test_audit_put_is_conditional`; cfn-lint + IAM policy test asserts no mutate verbs on audit ARN |
| F6 | Customer **IdP federation described but not deployed** (no `AWS::Cognito::UserPoolIdentityProvider`) | ✅ Confirmed | `security.yaml` has `IdpMetadataUrl` param but creates no external provider, claim mappings, domain, or callback URLs | Add `UserPoolIdentityProvider` (SAML/OIDC) + group→role claim mapping + hosted-UI domain + callback/logout URLs, gated by a `FederationEnabled` condition | cfn-lint; deploy-time conditional; documented Okta/Entra runbook |
| F7 | "**No data leaves the customer VPC**" is inaccurate: NAT + `0.0.0.0/0` egress, no Bedrock VPC endpoint, Lambdas not VPC-attached | ✅ Confirmed | `network.yaml` `NatGateway`, default route `0.0.0.0/0`, egress `-1 → 0.0.0.0/0`; no `VpcConfig` on functions; no `AWS::EC2::VPCEndpoint` | Either (a) implement: VPC-attach functions, Bedrock/S3/DynamoDB endpoints, restricted egress, flow logs; or (b) **correct the claim** to "customer-controlled VPC with configurable private connectivity" until (a) ships | cfn-lint; README claim matches template; endpoint inventory doc |
| F8 | **Container deploy path incomplete** — script omits image/module params; service has no reachable endpoint | ◑ Partially confirmed | `scripts/deploy.sh` `DEPLOY_MODE=container` but passes no `ImageUri`/`AgentModule`; `agent-service.yaml` has no ALB/health-check output | Either complete the ECS path (params + ALB + health check + output) **or** declare SAM/Lambda golden-path the single canonical path and mark container "reference-only" | Canonical-path decision recorded; deploy script validated for the chosen path |
| F9 | **CI fail-open** — native tests, prompt-manifest drift, and cfn-lint run with `\|\| true` | ✅ Confirmed | `.github/workflows/ci.yml` lines: native tests `\|\| true`, `prompt_registry \|\| true`, `cfn-lint … \|\| true` | Remove `\|\| true`; these become required, build-failing checks | CI goes red on injected drift / lint error (verified by a deliberate failing fixture in a throwaway branch) |
| F0 | **No single canonical deployment path** — README, scripts, templates, and native rebuild diverge | ✅ Confirmed | Three paths (shared CFN quickstart, per-agent SAM golden path, ECS container) described in parallel | Declare **per-agent SAM golden path** canonical for pilots; demote the others to "reference" with a one-line pointer; align README/scripts/diagrams | Doc review; one path passes the clean-account acceptance test below |

### P0 clean-account acceptance test (the gate)

A single automated test, run in a throwaway AWS account, must pass end-to-end and **fail at the first missing control**:

```
deploy → authenticate (federated user) → ingest fixture → run agent
       → REJECT unauthorized approval (wrong role / self-approval / tampered args / replay)
       → ACCEPT a valid bound approval → execute governed connector
       → verify immutable audit row (conditional-put, no-overwrite) → export evidence → destroy
```

Until this passes, the public framing is **"governed-agent reference architecture + pilot accelerator,"** not "deployable production solution," and the README must not say the audit trail "satisfies" 21 CFR Part 11 — only that it is "designed to support" Part 11 controls subject to customer CSV/CSA validation.

---

## P1 — before a regulated pilot

| # | Item | Verdict | Action |
|---|---|---|---|
| P1-1 | Shared execution role is broad | ✅ Confirmed (`security.yaml` one role) | Split into per-agent / per-function / per-connector least-privilege roles scoped to specific table, secret, model, guardrail, and connector ARNs |
| P1-2 | Edge & detection controls partial | ◑ | Wire WAF (exists in `edge.yaml`) into the canonical path; add API access logs, throttling, CloudTrail, GuardDuty, Security Hub, alarms, DLQs |
| P1-3 | Live connectors are reference adapters | ✅ Confirmed (fixture mode) | Build & test live adapters against vendor sandboxes; add idempotency, retries, reconciliation, failure-state recovery |
| P1-4 | No SLO/DR evidence | ✅ Confirmed | Define SLOs, RTO/RPO, backup-restore test, load test, fault-injection |
| P1-5 | Supply chain | ✅ Confirmed | Dependency lockfiles+hashes, secret scanning, SAST/SCA, IaC scan, container scan, SBOM, artifact/image signing, build provenance (NIST SSDF / SSDF AI profile) |
| P1-6 | No requirements-traceability matrix | ✅ Confirmed | Build an RTM: each claimed control → code → test → owner → customer-responsibility |
| P1-7 | No validation collateral | ✅ Confirmed | Intended-use docs + IQ/OQ/PQ templates where applicable |

---

## P2 — positioning (already partly addressed)

The repo already separates demo/pilot/production maturity and ships a CIO/CISO answer kit, so this is tuning, not rebuild:

- Lead with **one lighthouse workflow (Agent 02, Pharmacovigilance)** taken genuinely end-to-end; present the other eight as roadmap/extensibility until they meet the same acceptance criteria.
- Add a **capability matrix (Demo / Pilot / Production)** to the README and tag every feature: *implemented & tested · implemented, needs customer config · reference implementation · design pattern only · not yet implemented.*
- Replace any "nine production-ready agents" phrasing with the governed-control-plane + lighthouse framing.

---

## What the review got *right* vs. where it overshoots

**Right (validated in code):** F1, F2, F3, F4, F4b, F5, F6, F7, F9, F0 all reproduce. These are the load-bearing findings and they are correct.

**Nuance / partial credit the review didn't give:**
- The **bound-approval primitive already exists and is unit-tested** in `platform_core/.../approvals.py` and is enforced in the `platform_core` gateway — the work is *wiring it into the native path*, not building it from scratch.
- **Consequential commits are already withheld from every agent grant** (`policy.CONSEQUENTIAL_COMMITS`) and tested — the agent literally cannot hold `safety.submit_report`. The review's "approval not enforced" critique applies to the *human* finalize step, not the agent's tool grants.
- The **golden-path template already tightened audit IAM to per-function `PutItem`** (better than the shared `security.yaml` role the review cites) — though neither yet uses conditional-put immutability.

These nuances *reduce the effort* but **do not change the verdict**: the deployed path must enforce what `platform_core` proves.

---

## Execution status

P0 code-enforceable fixes (F1, F2, F3, F4, F4b, F5, F9, F0-decision) are being implemented now and verified against the
full test suite in-sandbox. The IaC-and-AWS-dependent items (F6 IdP federation, F7 VPC endpoints, F8 container path) are
specified here and require a sandbox AWS account to validate end-to-end via the clean-account acceptance test.

| Finding | State | Evidence |
|---|---|---|
| F0 canonical path | ✅ done | per-agent SAM golden path declared canonical; smoke test now asserts `SUBMITTED` |
| F1 connector finalize | ✅ done | `finalize._submit_report` routes through the governed connector Lambda when `SAFETY_CONNECTOR_FUNCTION` is set; smoke asserts submission |
| F2 approval enforcement | ✅ done | `finalize._verify_approval` verifies a bound token (sig/expiry/SoD/args/single-use); `STRICT_APPROVAL=1` fails closed. **7 new tests** |
| F3 identity trust | ✅ done | connector `_claims` reads authorizer first; body identity gated by `HCLS_LOCAL_TEST`. **4 new tests** |
| F4 / F4b data contract | ✅ done | review/approval keyed by `approval_id` across table+`hitl_notify`+golden-path; finalize reads `event["review"]` sibling; local round-trip verified |
| F5 audit immutability | ✅ done | conditional `PutItem` (`attribute_not_exists`) + fail-closed in connector; `UpdateItem`/`BatchWriteItem` dropped from audit/review IAM |
| F9 CI fail-closed | ✅ done | removed `\|\| true` on native tests + prompt drift; cfn-lint uses `--non-zero-exit-code error` |
| F6 IdP federation | ✅ done (code) · ◑ needs live run | `security.yaml`: `AWS::Cognito::UserPoolIdentityProvider` (SAML; OIDC documented) + `UserPoolDomain` + federated app-client wiring (SupportedIdentityProviders / AllowedOAuthFlows+Scopes / Callback+Logout URLs from new `CallbackUrl` param), all gated by Condition `FederationEnabled` (true when `IdpMetadataUrl` non-empty); `custom:hcls_role` claim mapping. **`W2001` for IdpMetadataUrl gone.** `docs/IDP-FEDERATION-RUNBOOK.md` (Okta + Entra). Threaded through `quickstart.yaml` + `scripts/deploy.sh`. **Live federated login is part of the clean-account acceptance test and cannot be run here.** |
| F7 network isolation | ✅ done (code) · ◑ needs live run | `network.yaml`: S3+DynamoDB **gateway** endpoints; **interface (PrivateLink)** endpoints for bedrock-runtime, secretsmanager, kms, logs, sns, states, lambda with a restrictive endpoint SG (443 from app SG only); app SG egress tightened `-1/all → 443`; **VPC Flow Logs**; NAT retained as a documented fallback. Lambdas **VPC-attached** via `VpcConfig` in golden-path `template.yaml` (Globals) + `agent-service.yaml` (per-function), threaded via `VpcSubnetIds`/`VpcSecurityGroupId` (golden) and `PrivateSubnets`/`AppSecurityGroupId` (shared). README claim corrected to "configurable, on by default". **cfn-lint E-clean.** **Endpoint reachability / packet-path verification needs a live VPC.** |
| F8 container path | ✅ done (code) · ◑ needs live run | Option (a): `agent-service.yaml` container mode is now a complete honest reference — **internal ALB + target group + listener + `/ping` health check + service-DNS output** (`AgentServiceEndpoint`); required `ContainerImageUri`/`AgentModule` params. `scripts/deploy.sh` **refuses container mode without `CONTAINER_IMAGE_URI`** (no silent broken stack). SAM golden path declared **canonical**; this path = scale-out reference (README + template header). **cfn-lint E-clean.** **ECS task health behind the ALB needs a live deploy + a built ARM64 image.** |
| P1 / P2 | _backlog_ | per the tables above |

**Verification:** full suite **503 tests green** in one command (was 492; +7 finalize approval-integrity, +4 connector identity); all templates cfn-lint clean of E-level findings (`cfn-lint infra/cloudformation/*.yaml infra/golden-path-*/template.yaml --non-zero-exit-code error` → exit 0; W2001 for `IdpMetadataUrl` and `VpcId` gone).

**F6/F7/F8 — what still requires a live AWS account.** The templates are validated structurally only (cfn-lint E-clean, YAML/structure review); **nothing was deployed**. Still pending a throwaway-account run of the P0 clean-account acceptance test: (F6) end-to-end federated login through Okta/Entra and the `custom:hcls_role` claim asserting into the gateway authorizer; (F7) confirming in-account AWS-service traffic actually resolves to and traverses the VPC endpoints (not NAT) and that VPC-attached Lambdas reach Bedrock/S3/DynamoDB/Secrets/KMS over PrivateLink with the 443-only SGs; (F8) an ECS task passing the internal-ALB `/ping` health check behind a real ARM64 image. These are deploy-time behaviours cfn-lint cannot prove.
