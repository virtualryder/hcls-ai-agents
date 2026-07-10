#!/usr/bin/env bash
# build_release_packet.sh — assemble an HONEST release evidence packet into release/<version>/.
#
# Anti-false-pass contract (this script's whole reason to exist):
#   * For EVERY artifact we first check the tool is actually installed with `command -v`.
#   * If a tool is MISSING we write "SKIPPED: <tool> not installed" into its output file, mark it
#     ✗ in MANIFEST.md, and FAIL the build (non-zero exit). We NEVER run a missing tool and we
#     NEVER emit a ✓ for a tool that did not run.
#   * If a tool RAN, its MANIFEST mark derives from the tool's real exit code: ✓ iff exit 0,
#     otherwise ✗ (real findings/errors). The build also exits non-zero if anything is not ✓.
#
# This is the opposite of the quarantined release/1.0.0-INVALID packet, whose MANIFEST marked
# everything ✓ while its files literally contained "command not found".
#
# Usage:
#   scripts/build_release_packet.sh [version]      # default version: 1.0.1
#   PYTHON=python scripts/build_release_packet.sh   # override the interpreter (Windows)
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

VERSION="${1:-1.0.1}"
OUT="release/${VERSION}"
mkdir -p "$OUT"
PY="${PYTHON:-python3}"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

MISSING=0     # a required tool was not installed -> build MUST fail
NOTGREEN=0    # some artifact is not a clean ✓ (missing tool OR findings/errors)
ROWS=()       # MANIFEST bullet rows, in order

add_row() { ROWS+=("- **$1** — \`$2\` $3"); }

# run_artifact <label> <tool-binary> <output-basename> <cmd...>
# Checks the tool exists; if not, records SKIPPED + ✗ + fails the build. Otherwise runs the
# command (stdout+stderr -> the output file) and marks ✓/✗ from its real exit code.
run_artifact() {
  local label="$1" tool="$2" fname="$3"; shift 3
  local path="$OUT/$fname"
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'SKIPPED: %s not installed\n' "$tool" > "$path"
    printf '  [SKIP] %-28s %s not installed\n' "$label" "$tool"
    add_row "$label" "$fname" "✗ (SKIPPED — $tool not installed)"
    MISSING=1; NOTGREEN=1
    return
  fi
  if "$@" > "$path" 2>&1; then
    # A clean tool (e.g. cfn-lint with no findings) can exit 0 with no output. Record that
    # explicitly so an empty artifact is never mistaken for a tool that failed to run.
    [ -s "$path" ] || printf 'PASS: %s exited 0 with no output (no findings).\n' "$tool" > "$path"
    printf '  [ OK ] %-28s exit 0\n' "$label"
    add_row "$label" "$fname" "✓"
  else
    local rc=$?
    printf '  [FAIL] %-28s exit %s (see %s)\n' "$label" "$rc" "$fname"
    add_row "$label" "$fname" "✗ (exit $rc — real findings/errors, review $fname)"
    NOTGREEN=1
  fi
}

echo "==> building release packet -> $OUT (version $VERSION)"

# 1. Test report — the full offline suite (no API key, no AWS).
run_artifact "Test report" "$PY" "test-report.txt" bash scripts/run_all_tests.sh

# 2. SAST — bandit over the platform core.
run_artifact "SAST (bandit)" bandit "bandit.txt" bandit -r platform_core -f txt

# 3. Dependency audit — pip-audit over the pinned lockfile.
run_artifact "Dependency audit (pip-audit)" pip-audit "pip-audit.txt" \
  pip-audit -r platform_core/requirements-lock.txt

# 4. IaC lint — cfn-lint over the CloudFormation templates.
run_artifact "IaC lint (cfn-lint)" cfn-lint "cfn-lint.txt" \
  cfn-lint infra/cloudformation/*.yaml infra/golden-path-*/template.yaml

# 5. IaC scan — checkov over infra.
run_artifact "IaC scan (checkov)" checkov "checkov.txt" checkov -d infra --compact

# 6. SBOM — CycloneDX over the lockfile. Special-cased because cyclonedx-py writes the SBOM to a
#    file via -o (so we cannot fold its stdout into the artifact) and we assert it is non-empty.
SBOM_FILE="$OUT/sbom.json"
if ! command -v cyclonedx-py >/dev/null 2>&1; then
  printf 'SKIPPED: cyclonedx-py not installed\n' > "$SBOM_FILE"
  printf '  [SKIP] %-28s cyclonedx-py not installed\n' "SBOM (CycloneDX)"
  add_row "SBOM (CycloneDX)" "sbom.json" "✗ (SKIPPED — cyclonedx-py not installed)"
  MISSING=1; NOTGREEN=1
else
  if cyclonedx-py requirements platform_core/requirements-lock.txt -o "$SBOM_FILE" \
       > "$OUT/sbom.log" 2>&1 && [ -s "$SBOM_FILE" ]; then
    rm -f "$OUT/sbom.log"
    printf '  [ OK ] %-28s exit 0 (%s bytes)\n' "SBOM (CycloneDX)" "$(wc -c < "$SBOM_FILE")"
    add_row "SBOM (CycloneDX)" "sbom.json" "✓"
  else
    printf 'SBOM generation FAILED — cyclonedx-py did not produce a non-empty SBOM.\n' > "$SBOM_FILE"
    [ -f "$OUT/sbom.log" ] && cat "$OUT/sbom.log" >> "$SBOM_FILE"
    rm -f "$OUT/sbom.log"
    printf '  [FAIL] %-28s empty/failed SBOM\n' "SBOM (CycloneDX)"
    add_row "SBOM (CycloneDX)" "sbom.json" "✗ (empty/failed SBOM — review sbom.json)"
    NOTGREEN=1
  fi
fi

# ---- MANIFEST -------------------------------------------------------------------------------------
if [ "$MISSING" -ne 0 ]; then
  OVERALL="❌ INVALID — one or more tools were not installed (SKIPPED). Do not ship this packet."
elif [ "$NOTGREEN" -ne 0 ]; then
  OVERALL="⚠️ INCOMPLETE — all tools ran, but some reported findings/errors (✗). Review before shipping."
else
  OVERALL="✅ COMPLETE — every tool ran and passed (all ✓)."
fi

{
  echo "# Release packet — hcls-ai-agents — ${VERSION}"
  echo "_Generated ${NOW}. AGP contract: 1.0._"
  echo
  echo "> **Every ✓/✗ below is derived from the real exit code of a tool that actually ran.**"
  echo "> A missing tool is recorded as \`SKIPPED\`, marked ✗, and fails the build — this packet can"
  echo "> never show a ✓ for a check that did not execute. Contrast \`release/1.0.0-INVALID/\`."
  echo
  echo "**Overall: ${OVERALL}**"
  echo
  for r in "${ROWS[@]}"; do echo "$r"; done
  echo
  echo "## Pointers (in-repo)"
  echo "- Clean-account deploy report: \`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md\`"
  echo "- Known limitations: each hero \`*/ASSURANCE-PACKET.md\` §Known limitations; \`NOT-CLAIMS.md\`"
  echo "- Maturity + connector tiers: \`MATURITY.yaml\`, \`docs/CONNECTOR-MATURITY.md\`"
  echo "- Governance conformance: \`AGP-CONFORMANCE.md\`"
  echo "- Upgrade notes: \`CHANGELOG.md\` (+ AGP migration notes in the Aegis versioning doc)"
} > "$OUT/MANIFEST.md"

echo "------------------------------------------------------------"
echo "$OVERALL"
echo "MANIFEST -> $OUT/MANIFEST.md"

# ---- exit code: honest gate -----------------------------------------------------------------------
if [ "$MISSING" -ne 0 ]; then
  echo "FAIL: at least one tool was not installed; packet is INVALID." >&2
  exit 2
fi
if [ "$NOTGREEN" -ne 0 ]; then
  echo "FAIL: at least one check reported findings/errors; review before shipping." >&2
  exit 1
fi
echo "OK: all checks passed."
exit 0
