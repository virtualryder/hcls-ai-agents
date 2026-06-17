# Integration Guide — Regulatory Writing Agent

The agent reaches every system of record through the MCP authorization gateway,
never a vendor SDK directly. Integration = implementing connectors + mapping IdP
roles + configuring the gateway policy.

## 1. Identity (IdP → roles)

Federate from Okta/Entra/AD via Cognito (or AgentCore Identity). Map groups:

| IdP group | Role claim (`custom:hcls_role`) | Can authorize |
|---|---|---|
| GRP-REG-AUTHORS | `REGULATORY_AUTHOR` | draft, read RIM/DMS |
| GRP-REG-APPROVERS | `REGULATORY_APPROVER` | + create submission draft (RIM write) |

## 2. Connectors

Implement typed methods in `platform_core/hcls_agent_platform/connectors/live.py`
(preserve fixture signatures). Resolve credentials via `get_secret`.

| `kind` | Methods | System |
|---|---|---|
| `rim` | `get_obligations`, `search_guidance`, `create_submission_draft` | Veeva Vault RIM |
| `dms` | `get_document`, `put_draft` | Veeva Vault / OpenText |

Switch with `CONNECTOR_MODE=live`.

## 3. Gateway policy

`mcp_gateway/policy.py` already grants this agent (`01-regulatory-writing`) the RIM/DMS
tools and marks `rim.create_submission_draft` / `dms.put_draft` high-risk (human approval).
Tighten `ROLE_ENTITLEMENTS` to match your org. In production these become AgentCore
Gateway targets + Identity scopes (see `infra/cloudformation/agentcore-gateway.yaml`).

## 4. LLM provider

Dev: `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`. Production: `LLM_PROVIDER=bedrock`
with a VPC endpoint and `BEDROCK_GUARDRAIL_ID` set (PHI + off-label filters) so no
content leaves the AWS account.

## 5. Persistence

Set `DATABASE_URL` for PostgresSaver (resumable HITL, durable audit). Without it the
demo uses in-memory checkpointing.

## 6. Validation

Run `pytest tests/` and the governance evals; capture the run as part of CSV evidence.
