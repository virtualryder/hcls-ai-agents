#!/usr/bin/env bash
#
# build_lambdas.sh — package every agent's native Lambda bundle and the shared
# connector bundle into deployable .zip files WITH their third-party dependencies
# vendored in. This fixes the classic "works locally, ImportError on AWS" gap:
# the function code alone is not enough; Strands and the platform_core package
# must travel inside the zip.
#
# Outputs (one per agent + one shared connector):
#   aws-native-reference/<AgentId>/build/lambdas.zip
#   aws-native-reference/_shared/connector/build/connector.zip
#
# Usage:
#   scripts/build_lambdas.sh                 # build all agents + connector
#   scripts/build_lambdas.sh 02-pharmacovigilance   # build one agent + connector
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NATIVE_DIR="$REPO_ROOT/aws-native-reference"
PLATFORM_PKG="$REPO_ROOT/platform_core/hcls_agent_platform"
PY="${PYTHON:-python3}"

AGENTS=(
  01-regulatory-writing 02-pharmacovigilance 03-clinical-trial-ops
  04-site-patient-matching 05-quality-capa 06-protocol-design
  07-rwe-heor 08-medical-affairs-msl
)
if [[ $# -ge 1 ]]; then AGENTS=("$1"); fi

echo "==> repo: $REPO_ROOT"
[[ -d "$PLATFORM_PKG" ]] || { echo "ERROR: platform_core not found at $PLATFORM_PKG"; exit 1; }

# ── shared connector bundle (one copy backs every gateway target) ────────────
build_connector() {
  local src="$NATIVE_DIR/_shared/connector"
  local stage; stage="$(mktemp -d)"
  echo "==> building connector.zip"
  cp "$src/handler.py" "$src/__init__.py" "$stage/"
  cp -r "$PLATFORM_PKG" "$stage/hcls_agent_platform"
  $PY -m pip install --quiet --target "$stage" -r "$src/requirements.txt" 2>/dev/null || true
  ( cd "$stage" && find . -name '__pycache__' -type d -prune -exec rm -rf {} + )
  mkdir -p "$src/build"
  ( cd "$stage" && zip -qr "$src/build/connector.zip" . )
  rm -rf "$stage"
  echo "    -> $src/build/connector.zip"
}

# ── per-agent native Lambda bundle ───────────────────────────────────────────
build_agent() {
  local agent="$1"
  local src="$NATIVE_DIR/$agent"
  [[ -d "$src" ]] || { echo "    skip: no native dir for $agent"; return; }
  local stage; stage="$(mktemp -d)"
  echo "==> building $agent/lambdas.zip"
  # Function code at zip root: lambdas/, core.py, strands_agent.py
  cp -r "$src/lambdas" "$stage/lambdas"
  [[ -f "$src/core.py" ]]          && cp "$src/core.py" "$stage/"
  [[ -f "$src/strands_agent.py" ]] && cp "$src/strands_agent.py" "$stage/"
  # Platform package (PHI masker, gateway, connectors) importable at root
  cp -r "$PLATFORM_PKG" "$stage/hcls_agent_platform"
  # Vendored third-party deps (Strands SDK etc.); boto3 is in the Lambda runtime
  if [[ -f "$src/requirements.txt" ]]; then
    $PY -m pip install --quiet --target "$stage" -r "$src/requirements.txt" 2>/dev/null || \
      echo "    WARN: pip install failed for $agent (deps may be missing at runtime)"
  fi
  ( cd "$stage" && find . -name '__pycache__' -type d -prune -exec rm -rf {} + )
  mkdir -p "$src/build"
  ( cd "$stage" && zip -qr "$src/build/lambdas.zip" . )
  rm -rf "$stage"
  echo "    -> $src/build/lambdas.zip"
}

build_connector
for a in "${AGENTS[@]}"; do build_agent "$a"; done

echo "==> done. Upload with scripts/deploy.sh (or aws s3 cp ... s3://<code-bucket>/)."
