# Release packet — hcls-ai-agents — 1.0.1
_Generated 2026-07-10T23:18:31Z. AGP contract: 1.0._

> **Every ✓/✗ below is derived from the real exit code of a tool that actually ran.**
> A missing tool is recorded as `SKIPPED`, marked ✗, and fails the build — this packet can
> never show a ✓ for a check that did not execute. Contrast `release/1.0.0-INVALID/`.

**Overall: ⚠️ INCOMPLETE — all tools ran, but some reported findings/errors (✗). Review before shipping.**

- **Test report** — `test-report.txt` ✓
- **SAST (bandit)** — `bandit.txt` ✗ (exit 1 — real findings/errors, review bandit.txt)
- **Dependency audit (pip-audit)** — `pip-audit.txt` ✓
- **IaC lint (cfn-lint)** — `cfn-lint.txt` ✓
- **IaC scan (checkov)** — `checkov.txt` ✗ (exit 1 — real findings/errors, review checkov.txt)
- **SBOM (CycloneDX)** — `sbom.json` ✓

## Pointers (in-repo)
- Clean-account deploy report: `evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`
- Known limitations: each hero `*/ASSURANCE-PACKET.md` §Known limitations; `NOT-CLAIMS.md`
- Maturity + connector tiers: `MATURITY.yaml`, `docs/CONNECTOR-MATURITY.md`
- Governance conformance: `AGP-CONFORMANCE.md`
- Upgrade notes: `CHANGELOG.md` (+ AGP migration notes in the Aegis versioning doc)
