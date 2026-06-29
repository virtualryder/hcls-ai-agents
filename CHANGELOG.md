# Changelog

All notable changes to the HCLS AI Agent Suite. The authoritative running snapshot is
`SUITE-STATUS.md`; this file is the released-version summary.

## [Unreleased]
### Added — Security & deployability deepening (SLG-parity pass)
- **CISO/CIO security answer kit:** `SECURITY.md`, `docs/THREAT-MODEL.md`,
  `docs/NIST-800-53-CONTROL-MATRIX.md`, `docs/OWASP-LLM-ATLAS-MAPPING.md`,
  `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`,
  `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`, and a README "CISO/CIO question index".
- **Defense in depth in code:** consequential commits (`safety.submit_report`, `qms.close_capa`,
  `mes.record_disposition`) **withheld from every agent grant** (`policy.CONSEQUENTIAL_COMMITS`),
  enforced by `test_consequential_actions_withheld_from_agents`; bound human-approval tokens
  (`mcp_gateway/approvals.py`: single-use, separation-of-duties, args-bound; `STRICT_APPROVAL` for prod).
- **One-command test harness:** `make test` / `scripts/run_all_tests.sh` runs all **492** tests across
  20 suites in one go; root `conftest.py` + `pytest.ini` for the shared suite.
- **Edge layer in IaC:** `infra/cloudformation/edge.yaml` (CloudFront + WAF + ACM) closes the
  previously-flagged "edge not in IaC" gap.
- Repo hygiene: `VERSION`, `SOURCES.md`, this `CHANGELOG.md`; `09-manufacturing-batch-review` added to
  the Lambda build list.

## [0.9.0] — prior
- Nine agents built to flagship depth (incl. 09 Manufacturing Batch-Review + a live path on 02), AWS-native
  rebuilds, cited AWS-style deck system + CIO board deck, ROI calculator, Dave's Cheat Sheet. See `SUITE-STATUS.md`.
