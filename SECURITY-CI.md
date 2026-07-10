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
| **pip-audit** (deps) | report-only | flips to blocking once deps are hash-pinned in `platform_core/requirements-lock.txt` |
| **Semgrep** (SAST rulesets) | report-only | flips to blocking once a ruleset (e.g. `p/ci`) is pinned + triaged |
| **Checkov** (IaC) | soft-fail | pre-existing reference-template findings surfaced, not blocking (harden templates, then remove `--soft-fail`) |
| **CycloneDX SBOM** | artifact | published every run |

The committed baselines record the CURRENT findings (audit `.secrets.baseline` with
`detect-secrets audit` to confirm the entries are false positives). New findings block the build.
EDU's `security.yml` is the enforcing reference; HCLS additionally runs a broader report-only
supply-chain job in `ci.yml` (gitleaks, Trivy, Terraform validate) — `security.yml` is the blocking gate.

### Bringing the last two to blocking

### How to enforce the remaining scanners

| Scanner | Make it blocking |
|---|---|
| **Bandit** | `bandit -r . --severity-level medium --confidence-level medium --skip B101 -f json -o .bandit-baseline.json`, commit the baseline, then run with `-b .bandit-baseline.json` and drop `|| true`. New medium+ findings then fail CI; baselined ones don't. |
| **detect-secrets** | `detect-secrets scan > .secrets.baseline`, **audit** it (`detect-secrets audit .secrets.baseline`) to mark the known false positives (`.env.example` placeholders, prompt SHA hashes), commit it, then run `--baseline .secrets.baseline` and drop `|| true`. |
| **pip-audit** | Pin dependencies with hashes into `platform_core/requirements-lock.txt` (`pip-compile --generate-hashes`), then drop `|| true` so a known-vulnerable dependency fails CI. |
| **Semgrep** | Pin a ruleset (e.g. `p/ci`, `p/python`), triage, then drop `|| true`. |
| **Checkov** | Harden the reference templates, then remove `--soft-fail` to enforce on IaC misconfigurations. |

## Dependency lockfiles

Add `platform_core/requirements-lock.txt` (hash-pinned) so pip-audit and the SBOM run against exact,
reproducible versions. Until then the harness falls back to the unpinned `requirements.txt` (advisory).

## Where the evidence goes

A tagged release collects these outputs into `release/<version>/` via `tools/build_release_packet.sh`
([`RELEASE-PACKET.md`](RELEASE-PACKET.md)). Runtime security proofs (masking, Guardrails, egress,
Access Analyzer, CloudWatch alarms, WORM) are captured at deploy time — see the hero
`SECURITY-EVIDENCE-PACK.md` and `RUNTIME-EVIDENCE-RUNBOOK.md`.
