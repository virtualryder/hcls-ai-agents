# Clean-Account Acceptance Report — HCLS AI Agents (9 golden paths)

Sanitized deployment evidence for the live validation claimed in the README and
`docs/GOLDEN-PATH-DEPLOY-NOTES.md`. Validation account ID and IAM user are redacted; raw CLI
JSON is available on request. All verification queries were read-only.

**Account:** `<VALIDATION-ACCOUNT-ID>` · **Region:** us-east-1 · **Run dates:** 2026-06-29/30 (UTC) · **Independently re-verified:** 2026-07-07/08 via AWS CLI.

## 1. Stack lifecycle — all 9 golden paths

Deployed via SAM (CloudTrail `ExecuteChangeSet` events), reached CREATE_COMPLETE, exercised, and
deleted:

| Stack | ExecuteChangeSet (UTC) | Deleted (UTC) |
|---|---|---|
| hcls-02-dev (pilot, ×2 cycles) | Jun 29 22:34–23:08 (6 events) | Jun 29 22:34 / 23:12 |
| hcls-03-dev, hcls-04-dev, hcls-09-dev | Jun 30 00:05 | Jun 30 00:09 |
| hcls-01/05/06/07/08-dev | Jun 30 00:19–00:30 (2 events each) | Jun 30 00:31–00:32 |

## 2. Runtime verification

Step Functions `StartExecution` CloudTrail events across the deploy windows (~20 events) confirm
each workflow ran Assemble → human gate → bound SoD approval → Finalize to `SUCCEEDED`, matching
the per-run log in `docs/GOLDEN-PATH-DEPLOY-NOTES.md` (a recovered execution ARN from the hcls-02
run also corroborates).

## 3. Teardown verification — including a found-and-fixed gap

Stacks and Retain-policy DynamoDB tables (`hcls-*-dev-audit`, `-pending-approvals`,
`-approval-consumption`) were removed as documented. A later account sweep (2026-07-08) found the
**ten Cognito user pools had survived stack deletion** (`hcls-01-dev` … `hcls-09-dev`,
`hcls-02-dev` ×2); all ten were deleted on 2026-07-08 and `list-user-pools` verified empty.
Root cause and the `destroy.sh` fix are documented in `docs/GOLDEN-PATH-DEPLOY-NOTES.md`
(post-run finding). Current state: zero `hcls-*` resources of any type remain.

## 4. Method

Read-only CLI (plus the two `delete-user-pool` cleanup calls noted above):
`cloudformation list-stacks`, `cloudtrail lookup-events` (ExecuteChangeSet / DeleteStack /
StartExecution), `dynamodb list-tables`, `cognito-idp list-user-pools`. Portfolio-level export:
`Projects-DR/evidence/AWS-CLEAN-ACCOUNT-EVIDENCE-2026-07-07.md` (kept outside the repo).
