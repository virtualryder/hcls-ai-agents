#!/usr/bin/env bash
# run_all_tests.sh — the ONE command that verifies the entire suite.
#
# The nine agents and their AWS-native rebuilds each reuse the package names
# `agent` / `tools` / `core`, so they must each run in their own Python process
# (duplicate top-level packages cannot coexist in one interpreter). This script
# runs every component in isolation and prints a single PASS/FAIL total.
#
#   scripts/run_all_tests.sh           # full offline suite (no API key, no AWS)
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export EXTRACT_MODE=demo CONNECTOR_MODE=fixture PYTHONPATH="platform_core:."
# Default to python on Windows (python3 is often the MS Store stub), python3 elsewhere.
if [ -z "${PYTHON:-}" ]; then
  case "$(uname -s)" in CYGWIN*|MINGW*|MSYS*) PY=python;; *) PY=python3;; esac
else
  PY="$PYTHON"
fi

SUITES=( "platform_core/tests" "governance/tests" )
for a in [0-9][0-9]-*-agent; do SUITES+=( "$a/tests" ); done
for a in aws-native-reference/[0-9][0-9]-*; do [ -d "$a/tests" ] && SUITES+=( "$a/tests" ); done

total=0; failed=0; fails=()
for s in "${SUITES[@]}"; do
  full=$($PY -m pytest "$s" -p no:cacheprovider 2>&1)
  summary=$(echo "$full" | grep -oE '[0-9]+ (passed|failed|error)[^,]*' | paste -sd', ' -)
  n=$(echo "$full" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1); n=${n:-0}
  total=$((total + n))
  if echo "$full" | grep -qE '[0-9]+ (failed|error)'; then failed=$((failed+1)); fails+=("$s :: $summary"); fi
  printf "  %-46s %s\n" "$s" "${summary:-no tests}"
done
echo "------------------------------------------------------------"
if [ "$failed" -eq 0 ]; then
  echo "✅ ALL GREEN — $total tests passed across ${#SUITES[@]} suites (no API key, no AWS)."
else
  echo "❌ $failed suite(s) failed; $total passed elsewhere:"; printf '   %s\n' "${fails[@]}"; exit 1
fi
