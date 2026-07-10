# Security CI — scanners, and the report-only -> blocking path

*This repo runs a standardized security harness (`.github/workflows/security.yml`): **Bandit** (Python
SAST), **pip-audit** (dependency CVEs), **detect-secrets** (secret scan), **Semgrep** (SAST rulesets),
**Checkov** (IaC), and a **CycloneDX SBOM**. Aligns with AGP conformance ([`AGP-CONFORMANCE.md`](AGP-CONFORMANCE.md))
and the release packet ([`RELEASE-PACKET.md`](RELEASE-PACKET.md)).*

## Current policy: report-only (adopt first, enforce after triage)

Scanners run on every push/PR but **do not block the build yet**. This is deliberate: flipping a
scanner to blocking *before* triaging its pre-existing findings red-lines CI and creates pressure to
suppress rather than fix. The EDU repo (`edu-ai-agents/.github/workflows/security.yml`) is the
**enforcing reference** — bandit/pip-audit/detect-secrets are blocking there against committed
baselines. Bring this repo to the same end-state with the steps below.

## How to enforce (per scanner)

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
