# DO NOT USE — release 1.0.0 is INVALID (quarantined)

This packet (formerly `release/1.0.0/`) is **false-passing** and must **never** be presented to a
customer, assessor, or AWS reviewer as evidence. It was generated on a machine that did **not** have
the security tooling installed, so its checkmarks are not backed by real tool runs.

## Why it is invalid

| Artifact | Claimed in MANIFEST | Reality in the files |
|---|---|---|
| `sbom.json` | ✓ SBOM (CycloneDX) | **0 bytes** — no bill of materials at all |
| `bandit.txt` | ✓ SAST clean | literally contains `bash: line 1: bandit: command not found` |
| `pip-audit.txt` | ✓ dependency audit clean | literally contains `... pip-audit: command not found` |
| `checkov.txt` | ✓ IaC scan clean | literally contains `... checkov: command not found` |

The MANIFEST marked **all six** artifacts ✓ even though four of them never ran. A green MANIFEST here
proves nothing — it records the absence of the tools, not the absence of findings.

## What to use instead

Use the regenerated, honest packet at **`release/1.0.1/`**, produced by
`scripts/build_release_packet.sh`. That builder checks each tool is actually installed
(`command -v`), writes `SKIPPED: <tool> not installed` and fails the build if a tool is missing, and
derives every ✓/✗ in its MANIFEST from real tool exit codes. It can never emit a ✓ for a tool that
did not run.

This directory is retained only as a record of the defect and is intentionally renamed with the
`-INVALID` suffix so it cannot be mistaken for a shippable version.
