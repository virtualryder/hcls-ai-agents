# MCP Authorization Gateway

The governed front door between agents and systems of record (RIM, DMS, Safety
DB, EDC, CTMS, eTMF, RWD, QMS, CRM). **No agent calls a vendor system directly.**
Every tool call passes through one enforcement point.

This package is the **reference logic for Amazon Bedrock AgentCore Gateway +
AgentCore Identity**. The decision, least-privilege, token, and audit semantics
are identical to what you deploy on AWS; each tool name maps 1:1 to an AgentCore
Gateway target.

## Enforcement order (fail-closed at every step)

1. **Authenticate** the acting user — verified IdP claims; deny on missing `sub`.
2. **Authorize** — deny-by-default with least-privilege intersection:
   `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]`.
   An agent can never exceed the human it acts for.
3. **Human approval** for high-risk (write/irreversible) tools — a verified
   reviewer identity is bound into the record (21 CFR Part 11 e-signature linkage).
4. **Mint** a short-lived token scoped to exactly that tool (no standing service
   account) — production: AgentCore Identity / STS.
5. **Invoke** via the connector framework (fixture or live).
6. **Audit** the attempt (ALLOW/DENY/PENDING_APPROVAL/ERROR), PHI-masked, with
   lineage to the system of record — production sink: append-only DynamoDB/QLDB.
7. **Fail closed** on any error.

## Why this maps to AgentCore Gateway

| This package | Amazon Bedrock AgentCore |
|---|---|
| `policy.TOOL_REGISTRY` entries | AgentCore Gateway **targets** |
| `policy.decide()` intersection | Gateway authorizer + AgentCore Identity scopes |
| `tokens.mint_scoped_token()` | AgentCore Identity short-lived credentials |
| `audit.GatewayAuditLog` | CloudTrail + append-only DynamoDB audit store |
| `connectors/*` | Gateway target backends (Lambda / OpenAPI / MCP servers) |

See `infra/cloudformation/agentcore-gateway.yaml` for the deployable target
registration, and `governance/tests/test_hitl_gates.py` for the enforced
human-approval behavior.

## Usage

```python
from hcls_agent_platform.mcp_gateway import MCPGateway

gw = MCPGateway()
res = gw.invoke(
    user_claims={"sub": "u-123", "custom:hcls_role": "PV_ANALYST"},
    agent_id="02-pharmacovigilance",
    tool="safety.submit_report",
    args={"case_id": "ICSR-DRAFT-0001"},
    # Separation of duties: the reviewer MUST be a different person than the
    # requester. A self-approval (reviewer sub == user sub) is rejected.
    approval={"approved": True, "reviewer": {"sub": "u-456", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}},  # required: high-risk
)
assert res.decision == "ALLOW"
```
