# Golden Paths — deploy any one agent from a single folder

Each `infra/golden-path-<agent>/` is a **self-contained AWS SAM stack** for one agent. An SA clones
the repo and runs three commands — no shared quickstart, no S3 staging — to stand up the real agent
behind a Cognito-authorized HTTP API, a Step Functions workflow with a `waitForTaskToken` human gate,
a PHI-tuned Bedrock Guardrail, an append-only audit table, and a pending-approvals table.

```bash
cd infra/golden-path-02-pharmacovigilance     # pick any agent below
./deploy.sh hcls-02-dev                        # sam build && sam deploy
./smoke_test.sh hcls-02-dev                    # start a run → approve the human gate (bound, SoD) → assert SUCCEEDED
./destroy.sh hcls-02-dev                        # sam delete (Retain-policy tables remain)
```

**Before your first deploy, read [`docs/GOLDEN-PATH-DEPLOY-NOTES.md`](../docs/GOLDEN-PATH-DEPLOY-NOTES.md)** — prereqs + the issues already found and fixed by deploying all nine end-to-end in a clean account.

**Prereqs:** AWS SAM CLI, **Python 3.12** on PATH (the Lambda runtime; `sam build` validates it), account credentials, Bedrock model access (see `docs/AWS-ACCOUNT-PREREQUISITES.md`).
Defaults to `ConnectorMode=fixture` (safe demo data) and `StrictApproval=1` (a bound, single-use,
separation-of-duties, args-bound approval token is required at the human gate).

| Folder | Agent | Reviewer role | Bright line (the agent never commits) |
|---|---|---|---|
| `golden-path-01-regulatory-writing`        | 01 Regulatory Writing | REGULATORY_APPROVER | what gets submitted |
| `golden-path-02-pharmacovigilance`         | 02 Pharmacovigilance | PV_MEDICAL_REVIEWER | the reportable case (`safety.submit_report` withheld) |
| `golden-path-03-clinical-trial-ops`        | 03 Clinical Trial Ops & TMF | CLINOPS_LEAD | the TMF/query disposition |
| `golden-path-04-site-patient-matching`     | 04 Site & Patient Matching | CLINOPS_LEAD | site selection & patient eligibility |
| `golden-path-05-quality-capa`              | 05 Quality / CAPA | QUALIFIED_PERSON | the CAPA closure (`qms.close_capa` withheld) |
| `golden-path-06-protocol-design`           | 06 Protocol Design | CLINOPS_LEAD | the protocol design |
| `golden-path-07-rwe-heor`                  | 07 RWE / HEOR | EPIDEMIOLOGIST | the analysis & conclusions |
| `golden-path-08-medical-affairs-msl`       | 08 Medical Affairs / MSL | MEDICAL_AFFAIRS_APPROVER | what reaches an HCP |
| `golden-path-09-manufacturing-batch-review`| 09 Manufacturing Batch-Review | QA_RELEASE | batch release (`mes.record_disposition` withheld) |

**What's in each folder:** `template.yaml` (SAM), `layer/Makefile` (builds the shared
`platform_core` + `governance` + agent `core.py` layer), `deploy.sh`, `destroy.sh`, `smoke_test.sh`,
`mint_approval.py` (reviewer stand-in that mints a bound, separation-of-duties approval token), and
`DEPLOY-GOLDEN-PATH.md`.

**Reference vs. production:** the connector runs in `fixture` mode; the reviewer UI is the
`mint_approval.py` stand-in; live connectors, CSV/CSA validation, and a penetration test are the
engagement (`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`). The shared CloudFormation
quickstart (`scripts/deploy.sh`) remains the multi-agent, edge-fronted path; these golden paths are
the fastest single-agent on-ramp.
