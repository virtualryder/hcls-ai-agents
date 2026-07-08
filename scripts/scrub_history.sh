#!/usr/bin/env bash
# =============================================================================
# scrub_history.sh — RUN MANUALLY (Git Bash on Windows, or any bash).
# Rewrites git history to purge deploy artifacts that leak the validation AWS
# account ID (<VALIDATION-ACCOUNT-ID>), then force-pushes. Coordinate before running:
# after this, anyone with an old clone must re-clone fresh.
#
# WHY: deleted deploy artifacts remain in history and contain the account ID.
# `exec_arn.txt` is UTF-16LE, so naive text/secret scanners miss it — but it is
# fully recoverable from the public repo via `git log --diff-filter=D` + `git show`.
#
# Artifacts purged (all under infra/golden-path-*/):
#   exec_arn.txt, d.log, d2.log, deploy_02.log, smoke_02.log, approval.json, cli.json
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."          # repo root
REPO_DIR="$(pwd)"
ACCOUNT_ID="${SCRUB_ACCOUNT_ID:-<VALIDATION-ACCOUNT-ID>}"   # override via env if needed

echo "== Repo: $REPO_DIR"
echo "== Step 0: safety mirror backup =="
BACKUP="../hcls-ai-agents-backup-$(date +%Y%m%d-%H%M%S).git"
git clone --mirror "$REPO_DIR" "$BACKUP"
echo "Backup at: $BACKUP  (delete once you've confirmed the scrub is good)"

echo "== Step 1: ensure git-filter-repo is installed =="
if ! git filter-repo --version >/dev/null 2>&1; then
  python -m pip install --user git-filter-repo || pip install --break-system-packages git-filter-repo
fi
git filter-repo --version

echo "== Step 2: enumerate every artifact path ever in history (auto) =="
git rev-list --all --objects \
  | awk '{print $2}' \
  | grep -E 'infra/golden-path-[^/]+/(exec_arn\.txt|d2?\.log|deploy_.*\.log|smoke_.*\.log|approval\.json|cli\.json)$' \
  | sort -u > /tmp/scrub-paths.txt || true
echo "Paths to purge:"; cat /tmp/scrub-paths.txt

echo "== Step 3: purge those paths from ALL history =="
# filter-repo removes 'origin' as a safety measure; we re-add it in Step 6.
git filter-repo --force --invert-paths --paths-from-file /tmp/scrub-paths.txt

echo "== Step 4: belt-and-suspenders text replacement (UTF-8) =="
printf '%s==><VALIDATION-ACCOUNT-ID>\n' "$ACCOUNT_ID" > /tmp/scrub-replace.txt
git filter-repo --force --replace-text /tmp/scrub-replace.txt
rm -f /tmp/scrub-replace.txt /tmp/scrub-paths.txt

echo "== Step 5: verify the ID is gone (UTF-8 and UTF-16LE) =="
u16=$(printf '%s' "$ACCOUNT_ID" | sed 's/./&\x00/g')
hits=0
while read -r obj; do
  if git cat-file -p "$obj" 2>/dev/null | grep -aq "$ACCOUNT_ID"; then echo "UTF-8 HIT: $obj"; hits=$((hits+1)); fi
  if git cat-file -p "$obj" 2>/dev/null | grep -aq "$u16";        then echo "UTF-16 HIT: $obj"; hits=$((hits+1)); fi
done < <(git rev-list --objects --all | awk '{print $1}')
if [ "$hits" -eq 0 ]; then echo "CLEAN — no account-ID occurrences remain in history."; else echo "WARNING: $hits hits remain — investigate before pushing."; exit 1; fi

echo "== Step 6: restore remote and force-push =="
cat <<INSTRUCTIONS

filter-repo removed the 'origin' remote. When ready to publish:

  git remote add origin https://github.com/virtualryder/hcls-ai-agents.git
  git push --force --all origin
  git push --force --tags origin

Then: delete old local clones and re-clone fresh (do NOT pull into an old clone).
Optionally ask GitHub Support to expire cached views of the old commits:
https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

Because the leaked value is only an AWS **account ID** (not a credential), rotation
is not required — but scrubbing removes it from public view as intended.
INSTRUCTIONS
