#!/usr/bin/env bash
# =============================================================================
# scrub_history.sh — RUN MANUALLY. Rewrites git history; requires a force-push.
# Coordinate with anyone who has cloned this repo before running.
#
# WHY: Deleted deploy artifacts remain in git history and contain the real
# validation AWS account ID. exec_arn.txt is UTF-16LE encoded, so most secret
# scanners (and naive grep) will NOT find the account ID in it. Anyone cloning
# the public repo can recover it with `git log --diff-filter=D` + `git show`.
#
# Files to purge from all history:
#   exec_arn.txt, d.log, deploy_02.log, smoke_02.log, approval.json, cli.json
# =============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Deliberately NOT hardcoded — committing the ID here would re-leak it.
ACCOUNT_ID="${SCRUB_ACCOUNT_ID:?Set SCRUB_ACCOUNT_ID env var to the 12-digit account ID to scrub}"

echo "== Step 0: safety backup (mirror clone) =="
BACKUP="../hcls-ai-agents-backup-$(date +%Y%m%d-%H%M%S).git"
git clone --mirror "$REPO_DIR" "$BACKUP"
echo "Backup at: $BACKUP"

echo "== Step 1: install git-filter-repo =="
pip install --user git-filter-repo || pip install --break-system-packages git-filter-repo

echo "== Step 2: purge artifact files from ALL history =="
cd "$REPO_DIR"
# filter-repo wants a fresh clone; --force overrides (we made a mirror backup).
git filter-repo --force --invert-paths \
  --path exec_arn.txt \
  --path d.log \
  --path deploy_02.log \
  --path smoke_02.log \
  --path approval.json \
  --path cli.json

echo "== Step 3: belt-and-braces text replacement (UTF-8 occurrences) =="
# Replaces any remaining literal account-ID strings in historical blobs.
# NOTE: --replace-text operates on raw bytes; the UTF-16 file is already gone
# via Step 2, but if you add more paths later, remember UTF-16LE encodes the
# ID as '8\x006\x004\x00...' and needs a separate byte-pattern rule.
echo "${ACCOUNT_ID}==><VALIDATION-ACCOUNT-ID>" > /tmp/replacements.txt
git filter-repo --force --replace-text /tmp/replacements.txt
rm /tmp/replacements.txt

echo "== Step 4: verify nothing remains =="
# Scan every blob in every commit for the ID in UTF-8 and UTF-16LE.
git rev-list --objects --all | awk '{print $1}' | while read -r obj; do
  git cat-file -p "$obj" 2>/dev/null | grep -aq "${ACCOUNT_ID}" && echo "UTF-8 HIT in $obj"
  git cat-file -p "$obj" 2>/dev/null | grep -aq "$(echo -n "$ACCOUNT_ID" | sed 's/./&\x00/g')" && echo "UTF-16 HIT in $obj"
done || true
echo "(no HIT lines above == clean)"

echo "== Step 5: restore remote and force-push =="
cat <<'INSTRUCTIONS'
filter-repo removes the 'origin' remote as a safety measure. When you are
ready to publish the rewritten history:

  git remote add origin git@github.com:virtualryder/hcls-ai-agents.git
  git push --force --all origin
  git push --force --tags origin

Then have any other clones re-clone fresh (do NOT pull into an old clone).
GitHub support can additionally purge cached views of the old commits:
https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
INSTRUCTIONS
