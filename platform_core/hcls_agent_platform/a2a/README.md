# Reference A2A Pattern (governed, identity-propagating, audited)

**A2A is not used by the current suite** — the eight agents are independent,
in-process LangGraph workflows (see `ENTERPRISE-PLATFORM.md` ADR-001). This package
is the worked example for **when multi-agent is needed**: a supervisor invoking a
specialist over a hop that stays governed.

## What it demonstrates

```python
from hcls_agent_platform.a2a import A2ASupervisor, A2ARequest

sup = A2ASupervisor("orchestrator")
res = sup.dispatch(A2ARequest(
    specialist_id="02-pharmacovigilance",
    user_claims={"sub": "u-pv-1", "custom:hcls_role": "PV_PROCESSOR"},  # the HUMAN
    tool="safety.get_case", args={"case_id": "ICSR-1"}, task="triage"))
assert res.gateway.decision == "ALLOW"
```

The supervisor forwards the **human's** verified claims (never its own) and the
specialist's tool call runs through the **same MCP gateway**. So the four invariants
hold automatically:

1. **Identity propagation** — authorized as the human, not the supervisor.
2. **Least-privilege intersection** — `AGENT_TOOL_GRANTS[specialist] ∩ ROLE_ENTITLEMENTS[human]`; a supervisor cannot widen the human's permissions.
3. **Every hop audited** — an `A2A_DISPATCH` record (with `session_id` + `on_behalf_of`) plus the gateway's tool-call decision, linked by `session_id`.
4. **Human gates preserved** — a high-risk tool reached via the specialist still returns `PENDING_APPROVAL` until a verified human approves.

`tests/test_a2a.py` proves all four (incl. "supervisor cannot widen permissions"
and "specialist cannot exceed its own grants via A2A").

## Mapping to AWS

| This package | Amazon Bedrock AgentCore |
|---|---|
| `A2ASupervisor.dispatch()` hop | AgentCore Runtime endpoint invocation (specialist as a runtime) |
| forwarding the human's claims | AgentCore Identity (token carries the human, not the supervisor) |
| gateway authorize + audit | AgentCore Gateway + the append-only audit store |
| `session_id` across hops | AgentCore Observability trace |

**The rule for any engagement:** A2A runs *through* AgentCore — never around it.
