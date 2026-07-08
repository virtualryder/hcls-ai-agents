# Deploying the golden paths — prereqs, the proven flow, and lessons

> Every agent's golden path was deployed and run **end-to-end in a clean AWS account**
> (us-east-1) and torn down. This note captures exactly what an SA needs so the next deploy
> hits none of the issues we already fixed. All nine reached `CREATE_COMPLETE` and ran the full
> Assemble → … → human gate → bound approval → Finalize flow to `SUCCEEDED`.

## Prerequisites (have these before you start)

- **AWS CLI v2** and **AWS SAM CLI** on PATH, with working credentials (`aws sts get-caller-identity`).
- **Python 3.12** available to SAM. The Lambda runtime is `python3.12`; `sam build` validates the
  interpreter. If you only have another version, you can skip `sam build` entirely (see below) —
  the functions are dependency-free, so `sam deploy` packages them directly.
- **`python-dateutil`** importable by whatever Python runs `sam` (a botocore dependency). If
  `sam deploy` dies with `ModuleNotFoundError: No module named 'dateutil'`, run
  `python -m pip install python-dateutil` against the interpreter behind your `sam` shim.
- **`boto3`** if you use the `infra/_smoke/resume_any.py` helper to drive the human gate.
- **Bedrock model access** only matters for *live* narrative drafting. The drafter falls back to a
  deterministic demo narrative on any Bedrock error, so deployability does **not** depend on it.
  (The shipped default model id may be EOL in your account — set `BedrockModelId` to a current model
  for live mode; the workflow runs either way.)

## The proven deploy → smoke → destroy flow

```bash
cd infra/golden-path-02-pharmacovigilance      # any agent
bash prepare_layer.sh                            # stage platform_core + governance + agent modules into layer/python/
sam deploy --stack-name hcls-02-dev --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --resolve-s3 --no-confirm-changeset --no-fail-on-empty-changeset \
  --parameter-overrides Environment=dev ConnectorMode=fixture
# smoke: start an execution, approve the human gate with a BOUND approval, assert SUCCEEDED
python ../_smoke/resume_any.py <executionArn> "$PWD"
# destroy
aws cloudformation delete-stack --stack-name hcls-02-dev --region us-east-1
# the audit / pending-approvals / approval-consumption tables are DeletionPolicy:Retain — delete them too:
for t in audit pending-approvals approval-consumption; do aws dynamodb delete-table --table-name hcls-02-dev-$t --region us-east-1; done
```

`NetworkMode=PrivateOnly` (default) creates **no NAT** — cheapest footprint. The Retain-policy tables
survive `delete-stack` by design; delete them explicitly to avoid orphan tables (the
`approval-consumption` table only exists for Agent 02 today).

## Lessons (issues already fixed — here so you recognize them)

1. **`sam build` needs Python 3.12.** No 3.12 and no Docker? Skip `sam build` — `sam deploy` packages
   the (dependency-free) source directly. The layer must be pre-staged first via `prepare_layer.sh`.
2. **The shared layer is pre-staged, not built by a Makefile.** `prepare_layer.sh` copies
   `platform_core` + `governance` + **all** agent-root modules (`core.py` *and* `strands_agent.py`)
   into `layer/python/`. A missing module shows up only at runtime as `No module named '…'`.
3. **Bedrock Guardrail:** `PROMPT_ATTACK` filter **OutputStrength must be `NONE`** (it's an
   input-only filter). `HIGH` makes the guardrail (and the whole stack) roll back.
4. **Two ASL data contracts — don't cross them.**
   - *Family A* (02/03/04/09): tasks use a **direct function-ARN** resource and return
     `{statusCode, body:"<json string>"}`. The ASL parses it with
     `ResultSelector: States.StringToJson($.body)` so `$.body.routing.next` resolves.
   - *Family B* (01/05/06/07/08): tasks use `arn:aws:states:::lambda:invoke` with
     `OutputPath:"$.Payload"` and **bare-dict passthrough** (`_shared.ok` returns the state dict,
     no `body` wrapper), so `$.routing.next` is already at the root. **Do not** add a body-parse
     here — there is no `body`.
5. **Identity lineage:** `assemble` carries `requestor`/`acting_user_claims` through the pipeline so
   the consequential-action requestor at Finalize matches the approval binding (separation of duties).
6. **Human-authority commit:** consequential commits (`safety.submit_report`, `qms.close_capa`,
   `mes.record_disposition`) are withheld from every agent grant. The human-approved commit is
   authorized by the **approver's role + a bound approval** (`policy.decide_human_commit` +
   the gateway human-commit path), and runs through the governed connector via a **direct
   (IAM-authenticated) invoke** — the connector trusts payload identity only when there is no
   `requestContext` (i.e. not a network request). Finalize verifies the approval with `consume=False`;
   the connector is the durable single-use enforcement point.
7. **SAM only re-pushes a state machine when the ASL *content* changes** — not when only
   `DefinitionSubstitutions` change. If a definition edit isn't taking effect, change the ASL file
   itself (and confirm with `aws stepfunctions describe-state-machine ... --query definition`).
8. **Agent 07** names its draft step `Synthesize`; its ASL points at `${DraftFunctionArn}` (the
   deployed `DraftFn`). If you re-template it, keep that mapping.
9. **Driving the human gate from a script:** pass the SendTaskSuccess output via boto3 (or
   `--cli-input-json file://`), never as a raw `--task-output` string — shells mangle the embedded
   JSON quotes. `infra/_smoke/resume_any.py` does this and reuses each agent's `mint_approval.py`.

## What a green smoke proves (and doesn't)

Proves: the stack deploys clean in a new account; the governed workflow runs; the human/QA gate
fires and only resumes on a bound, separation-of-duties approval; the consequential commit is
authorized by the human (never the agent); the immutable `INTENT → COMMITTED` audit trail and the
durable single-use approval registry are written. Does **not** prove: federated IdP login, live
vendor-system integration, CSV/CSA validation, or a penetration test — those remain the engagement.

## Post-run finding (2026-07-08): Cognito user pools survived teardown

A later account sweep found all ten Cognito user pools from the 2026-06-29/30 golden-path runs
(`hcls-01-dev` … `hcls-09-dev`, `hcls-02-dev` x2) still live after stack deletion — user pools
were retained on stack delete while stacks and Retain-policy DynamoDB tables had been cleaned up.
All ten were deleted manually on 2026-07-08 (`cognito-idp delete-user-pool`); `list-user-pools`
verified empty.

**Fix for future runs:** either remove the Retain behavior on the user pool for dev golden paths,
or add an explicit user-pool cleanup step to each `destroy.sh`:

    POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 \
      --query "UserPools[?Name=='<stack-name>'].Id" --output text)
    [ -n "$POOL_ID" ] && aws cognito-idp delete-user-pool --user-pool-id "$POOL_ID"

and extend the teardown verification checklist to include `cognito-idp list-user-pools`.
