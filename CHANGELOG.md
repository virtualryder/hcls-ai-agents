# Changelog

All notable changes to the HCLS AI Agent Suite. The authoritative running snapshot is
`SUITE-STATUS.md`; this file is the released-version summary.

## [Unreleased]
### Added — External-review remediation (P0)
Independent review (scored 58/100) flagged gaps between the control narrative and the
*deployed* path. All P0 items below are closed and verified.
- **Human-approval integrity on the deployed path** — the AWS-native `finalize` now verifies a
  **bound approval token** (signature, expiry, separation of duties, exact-args, single-use) and
  **fails closed** under `STRICT_APPROVAL=1`; the consequential submit routes through the governed
  connector instead of a stub (`aws-native-reference/02-pharmacovigilance/lambdas/finalize.py`).
- **Identity trust (F3)** — the shared connector resolves identity/role from the authenticated
  authorizer context, never request-body fields (gated by `HCLS_LOCAL_TEST`).
- **Data contract (F4/F4b)** — review/approval unified on `approval_id`; `finalize` reads the
  reviewer decision from the ASL sibling.
- **Immutable, fail-closed audit (F5)** — conditional `PutItem` (`attribute_not_exists`); `UpdateItem`/
  `BatchWriteItem` removed from the audit/review IAM grants.
- **Customer IdP federation (F6)** — real `AWS::Cognito::UserPoolIdentityProvider` (SAML/OIDC) +
  hosted-UI domain + group→`custom:hcls_role` mapping, gated by `FederationEnabled`; new
  `docs/IDP-FEDERATION-RUNBOOK.md` (Okta + Entra ID).
- **Network isolation (F7)** — S3/DynamoDB gateway endpoints + PrivateLink interface endpoints
  (bedrock-runtime, secrets, KMS, logs, SNS, Step Functions, Lambda), VPC Flow Logs, 443-only
  egress, VPC-attached Lambdas; the inaccurate "no data leaves the VPC" claim corrected to accurate
  "configurable, on by default" framing.
- **Container path (F8)** — `agent-service.yaml` completed with an internal ALB + `/ping` health
  check + service-DNS output; `deploy.sh` refuses container mode without an image URI; the per-agent
  **SAM golden path is declared canonical**.
- **CI fail-closed (F9)** — removed `|| true` on native tests + prompt-drift; cfn-lint uses
  `--non-zero-exit-code error`.
- **Tests:** suite **492 → 536** (+7 finalize approval-integrity, +4 connector identity).

### Added — Security & deployability deepening (SLG-parity pass)
- **CISO/CIO security answer kit:** `SECURITY.md`, `docs/THREAT-MODEL.md`,
  `docs/NIST-800-53-CONTROL-MATRIX.md`, `docs/OWASP-LLM-ATLAS-MAPPING.md`,
  `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`,
  `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`, and a README "CISO/CIO question index".
- **Defense in depth in code:** consequential commits (`safety.submit_report`, `qms.close_capa`,
  `mes.record_disposition`) **withheld from every agent grant** (`policy.CONSEQUENTIAL_COMMITS`),
  enforced by `test_consequential_actions_withheld_from_agents`; bound human-approval tokens
  (`mcp_gateway/approvals.py`: single-use, separation-of-duties, args-bound; `STRICT_APPROVAL` for prod).
- **One-command test harness:** `make test` / `scripts/run_all_tests.sh` runs all **536** tests across
  20 suites in one go; root `conftest.py` + `pytest.ini` for the shared suite.
- **Edge layer in IaC:** `infra/cloudformation/edge.yaml` (CloudFront + WAF + ACM) closes the
  previously-flagged "edge not in IaC" gap.
- Repo hygiene: `VERSION`, `SOURCES.md`, this `CHANGELOG.md`; `09-manufacturing-batch-review` added to
  the Lambda build list.

## [0.9.0] — prior
- Nine agents built to flagship depth (incl. 09 Manufacturing Batch-Review + a live path on 02), AWS-native
  rebuilds, cited professional deck system + CIO board deck, ROI calculator, Dave's Cheat Sheet. See `SUITE-STATUS.md`.
