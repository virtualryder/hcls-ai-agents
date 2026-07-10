# Security CI — scanners, and the report-only -> blocking path

*This repo runs a standardized security harness (`.github/workflows/security.yml`): **Bandit** (Python
SAST), **pip-audit** (dependency CVEs), **detect-secrets** (secret scan), **Semgrep** (SAST rulesets),
**Checkov** (IaC), and a **CycloneDX SBOM**. Aligns with AGP conformance ([`AGP-CONFORMANCE.md`](AGP-CONFORMANCE.md))
and the release packet ([`RELEASE-PACKET.md`](RELEASE-PACKET.md)).*

## Current policy

| Scanner | Status | Basis |
|---|---|---|
| **Bandit** (SAST) | **BLOCKING** | vs committed `.bandit-baseline.json` — a NEW medium+ finding fails CI; baselined findings don't |
| **detect-secrets** | **BLOCKING** | vs committed `.secrets.baseline` — a NEW unbaselined secret fails CI |
| **pip-audit** (deps) | **BLOCKING** | deps are hash-pinned in `platform_core/requirements-lock.txt`; a known-vulnerable dependency now fails CI (the `\|\| true` was dropped) |
| **Semgrep** (SAST rulesets) | report-only | flips to blocking once a ruleset (e.g. `p/ci`) is pinned + triaged |
| **Checkov** (IaC) | soft-fail | pre-existing reference-template findings surfaced, not blocking (harden templates, then remove `--soft-fail`) |
| **CycloneDX SBOM** | artifact | published every run |

The committed baselines record the CURRENT findings (audit `.secrets.baseline` with
`detect-secrets audit` to confirm the entries are false positives). New findings block the build.
EDU's `security.yml` is the enforcing reference; HCLS additionally runs a supply-chain job in
`ci.yml` (gitleaks, Trivy, Terraform validate). **Trivy is now blocking** — the filesystem
vulnerability + secret scan runs with `exit-code: "1"`, so a CRITICAL/HIGH vuln or a leaked secret
fails the job (was previously non-blocking / exit-code 0). `security.yml` remains the primary
blocking gate.

### How to enforce the remaining scanners

pip-audit and Trivy are now blocking (see above). The two that remain non-blocking are Semgrep
(report-only) and Checkov (soft-fail).

| Scanner | Status / to enforce |
|---|---|
| **Bandit** | **BLOCKING.** Runs `-b .bandit-baseline.json`; new medium+ findings fail CI, baselined ones don't. |
| **detect-secrets** | **BLOCKING.** Runs `--baseline .secrets.baseline` (audited for the `.env.example` placeholders + prompt SHA hashes); a new unbaselined secret fails CI. |
| **pip-audit** | **BLOCKING.** Deps are hash-pinned in `platform_core/requirements-lock.txt` (`pip-compile --generate-hashes`) and the `\|\| true` was dropped, so a known-vulnerable dependency fails CI. |
| **Trivy** | **BLOCKING.** Runs with `exit-code: "1"` on CRITICAL/HIGH vulns + leaked secrets. |
| **Semgrep** | report-only. Pin a ruleset (e.g. `p/ci`, `p/python`), triage, then drop `\|\| true`. |
| **Checkov** | soft-fail. Harden the reference templates, then remove `--soft-fail` to enforce on IaC misconfigurations. |

## Dependency lockfiles

`platform_core/requirements-lock.txt` (hash-pinned) is committed, so pip-audit and the SBOM run
against exact, reproducible versions and pip-audit enforces (blocking) rather than advising.

## Where the evidence goes

A tagged release collects these outputs into `release/<version>/` via `tools/build_release_packet.sh`
([`RELEASE-PACKET.md`](RELEASE-PACKET.md)). Runtime security proofs (masking, Guardrails, egress,
Access Analyzer, CloudWatch alarms, WORM) are captured at deploy time — see the hero
`SECURITY-EVIDENCE-PACK.md` and `RUNTIME-EVIDENCE-RUNBOOK.md`.
