# Integration Guide — Pharmacovigilance ICSR Intake Agent

The agent reaches every system of record through the MCP authorization gateway,
never a vendor SDK directly. Integration = implementing connectors + mapping IdP
roles + configuring the gateway policy.

## 1. Identity (IdP → roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-PV-PROCESSORS | `PV_PROCESSOR` | read safety DB, code terms, write case draft |
| GRP-PV-REVIEWERS | `PV_MEDICAL_REVIEWER` | + submit ICSR (irreversible write) |

## 2. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Methods | System |
|---|---|---|
| `safety` | `get_case`, `search_duplicates`, `write_case_draft`, `submit_report` | Argus Safety, Veeva Safety, Oracle Empirica |
| `meddra` | `code_term` | MSSO MedDRA Browser API |
| `whodrug` | `code_drug` | UMC WHODrug API |

Switch with `CONNECTOR_MODE=live`.

## 3. Gateway policy

`platform_core/hcls_agent_platform/mcp_gateway/policy.py` already grants agent
`02-pharmacovigilance` the safety/MedDRA/WHODrug tools. `safety.write_case_draft`
and `safety.submit_report` are marked `high_risk=True` (human approval required).
Tighten `ROLE_ENTITLEMENTS` to match your org.

## 4. Safety database integration

### Argus Safety (Oracle)
Connect via Argus Web Service API. Map case fields to Argus schema using
`write_case_draft`; submission triggers the Argus workflow queue.

### Veeva Safety
Use Veeva Vault REST API. `get_case` reads from the case vault; `submit_report`
creates a new case version in the submission state.

### E2B(R3) transmission
For EMA EVWEB / FDA ESG submission, the connector must serialize the extracted
fields + coded terms + narrative to ICH E2B(R3) XML before `submit_report`.
That serialization belongs in the connector, not the agent.

## 5. Medical dictionary integration

### MedDRA (MSSO)
Obtain a license from the MSSO. Implement `meddra.code_term` against the MedDRA
Browser REST API or local SQLite browser. Map returned PT + SOC to state fields.

### WHODrug (Uppsala Monitoring Centre)
Obtain a license from the UMC. Implement `whodrug.code_drug` against the WHODrug
Global API. Map returned preferred name + ATC to state fields.

## 6. LLM provider

Dev: `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`. Production: `LLM_PROVIDER=bedrock`
with a VPC endpoint and `BEDROCK_GUARDRAIL_ID` set (PHI filter required — ICSR source
records contain patient PII) so no content leaves the AWS account.

## 7. Persistence

Set `DATABASE_URL` for PostgresSaver (resumable HITL, durable case state). Without it
the demo uses in-memory checkpointing. GVP requires case retention for the product
lifetime + 10 years; use S3 Object Lock or QLDB for the finalized audit trail.

## 8. Validation

Run `pytest tests/` and the governance evals; capture the run as part of CSV evidence.
Validate the coding fixture against your licensed MedDRA/WHODrug versions.
