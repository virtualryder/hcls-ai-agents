#!/usr/bin/env bash
# Tear down the golden-path stack. The audit + pending tables are Retain (PITR); export evidence first.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-hcls-08-dev}"
REGION="${AWS_REGION:-us-east-1}"
sam delete --stack-name "$STACK" --region "$REGION" --no-prompts
echo "Deleted $STACK (Retain-policy tables remain — remove deliberately)."
