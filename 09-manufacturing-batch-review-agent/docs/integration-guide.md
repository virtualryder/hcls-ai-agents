# Agent 09 — Integration Guide

## Systems of record (new connectors)
| System | Kind | Operations (gateway tools) | Risk |
|---|---|---|---|
| MES / electronic batch records (Körber, Tulip, Rockwell, AVEVA, Honeywell) | `mes` | `mes.get_batch_record` (read) · `mes.write_disposition_draft` (write) · `mes.record_disposition` (write/irreversible) | read / write |
| LIMS (LabWare, STARLIMS, Benchling LIMS) | `lims` | `lims.get_results` (read) | read |

All access flows through the **MCP authorization gateway** — no agent calls a vendor API directly.
Tool names map 1:1 to AgentCore Gateway targets. The connector interface is identical in fixture and
live mode (`CONNECTOR_MODE`), so agent code does not change between demo and production.

## Roles (least-privilege intersection)
- **MFG_OPERATOR** — read batch + LIMS, draft a disposition. **Cannot** record the disposition.
- **QA_RELEASE** (Qualified Person / QA reviewer) — operator rights **plus** the irreversible
  `mes.record_disposition` (release/reject), which additionally requires a human-approval binding.

An agent can never exceed the human it acts for: `permitted(tool) ⇔ agent-grant ∩ user-entitlement`.

## Going live
1. Set `CONNECTOR_MODE=live` and implement `LiveMES` / `LiveLIMS` in
   `platform_core/.../connectors/live.py` against the customer's MES/LIMS API (mirror `LiveSafetyConnector`).
2. Provide `MES_BASE_URL` / `LIMS_BASE_URL` (+ tokens via Secrets Manager).
3. Map the customer's IdP roles to `MFG_OPERATOR` / `QA_RELEASE` via the Cognito claim
   (`AUTH_ROLE_CLAIM`, default `custom:hcls_role`).
4. Confirm the batch-record schema matches the scanner's expectations (steps with
   `value/lo/hi/signed/critical`, `required_steps`, and LIMS `result/lo/hi/status`); adapt the
   connector's response mapping, not the agent.

## Batch-record / LIMS schema (fixture contract)
```
batch_record = {batch_id, product, required_steps: [id...],
                steps: [{id, name, value, lo, hi, unit, signed, critical}]}
lims_results = [{test, result, lo, hi, unit, status}]   # status PASS|OOS
```
