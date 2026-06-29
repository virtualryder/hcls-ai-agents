#!/usr/bin/env bash
# Pre-stage the shared Lambda layer BEFORE `sam build`. Run from this folder.
set -euo pipefail
cd "$(dirname "$0")"
REPO="../.."
AGENT="08-medical-affairs-msl"
rm -rf layer/python
mkdir -p layer/python
cp -r "$REPO/platform_core/hcls_agent_platform" layer/python/
cp -r "$REPO/governance" layer/python/
cp "$REPO/aws-native-reference/$AGENT/core.py" layer/python/
echo "layer staged for $AGENT"
