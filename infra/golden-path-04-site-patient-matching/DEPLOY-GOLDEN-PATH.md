# Golden Path — 04 Site Selection & Patient Matching (one command)

Deploys the **real** Agent 02 workflow as a self-contained SAM stack: a shared layer
(`platform_core` + `governance` + the agent `core.py`), the five workflow Lambdas
(assemble → draft → check → **human gate** (`waitForTaskToken`) → finalize), the governed
connector Lambda (the deployed gateway enforcement point), the native Step Functions state
machine, an HTTP API with a Cognito JWT authorizer + access logging + throttling, a PHI-tuned
Bedrock Guardrail (prompt-attack in+out), an append-only audit table, and a pending-approvals table.

```bash
cd infra/golden-path-04-site-patient-matching
./deploy.sh hcls-04-dev          # sam build && sam deploy
./smoke_test.sh hcls-04-dev      # start execution → approve human gate (bound, SoD) → assert SUCCEEDED
./destroy.sh hcls-04-dev         # sam delete (Retain tables remain)
```

**Prereqs:** AWS SAM CLI, account credentials, Bedrock model access enabled (see
`docs/AWS-ACCOUNT-PREREQUISITES.md`). Runs in `ConnectorMode=fixture` (safe demo data) by default.

**The bright line, in code:** the irreversible ICSR submission (`safety.submit_report`) is
**withheld from the agent** (`policy.CONSEQUENTIAL_COMMITS`); the agent records a draft and a
qualified person commits. `StrictApproval=1` (default) requires a bound, single-use,
separation-of-duties, args-bound approval token at the human gate.

**Production next steps (the engagement):** swap `ConnectorMode=live` against Argus/Veeva Safety,
add the reviewer service UI (the `mint_approval.py` stand-in mints the bound token here), complete
CSV/CSA, and run a penetration test. See `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
