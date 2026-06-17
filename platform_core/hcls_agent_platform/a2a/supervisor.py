"""
Reference A2A supervisor — a governed agent-to-agent hop.

Invariants enforced here (ADR-001):
  1. IDENTITY PROPAGATION — the hop carries the original human's verified claims,
     never the supervisor agent's identity. The specialist is authorized as the
     human, so it can never gain elevated permissions by being called.
  2. LEAST-PRIVILEGE INTERSECTION STILL APPLIES — the specialist's tool call goes
     through the same MCP gateway, which authorizes against
     AGENT_TOOL_GRANTS[specialist] ∩ ROLE_ENTITLEMENTS[human]. A supervisor cannot
     widen what the human may do.
  3. EVERY HOP IS AUDITED — an A2A_DISPATCH record (with session_id + on_behalf_of)
     is written, then the gateway records the tool decision. Both share session_id.
  4. HUMAN GATES PRESERVED — a high-risk tool reached via a specialist still returns
     PENDING_APPROVAL until a verified human approves; A2A cannot skip the gate.

On AWS this maps to: the A2A hop = an AgentCore Runtime endpoint invocation; the
human's claims travel via AgentCore Identity; authorization + audit are the same
AgentCore Gateway path used for any tool call. This module is the deterministic,
testable model of that behavior.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from hcls_agent_platform.mcp_gateway import MCPGateway, GatewayResult


@dataclass
class A2ARequest:
    """A supervisor's request to a specialist agent."""
    specialist_id: str                       # e.g. "02-pharmacovigilance"
    user_claims: Dict[str, Any]              # the ORIGINAL human's verified IdP claims
    tool: str                                # the system-of-record op the specialist will run
    args: Dict[str, Any] = field(default_factory=dict)
    approval: Optional[Dict[str, Any]] = None  # verified human approval for high-risk tools
    task: str = ""                           # human-readable description (lineage only)
    session_id: Optional[str] = None         # links the whole workflow; auto if absent


@dataclass
class A2AResult:
    session_id: str
    supervisor_id: str
    specialist_id: str
    dispatch_audit_id: str
    gateway: GatewayResult                   # the specialist's gateway decision/result


class A2ASupervisor:
    """
    Dispatches work to specialist agents over a governed A2A hop.

    The supervisor has NO standing authority of its own: it forwards the human's
    claims and the gateway decides. It cannot elevate, cannot bypass approval, and
    every hop it makes is recorded.
    """

    def __init__(self, supervisor_id: str, gateway: Optional[MCPGateway] = None) -> None:
        self.supervisor_id = supervisor_id
        self.gateway = gateway or MCPGateway()

    def dispatch(self, req: A2ARequest, *, raise_on_deny: bool = False) -> A2AResult:
        session_id = req.session_id or f"sess-{uuid.uuid4()}"

        # Guard: the hop must carry a real human identity, not the supervisor's.
        sub = (req.user_claims or {}).get("sub")
        if not sub or sub == self.supervisor_id:
            aid = self.gateway.audit.record({
                "decision": "DENY", "tool": req.tool, "agent_id": req.specialist_id,
                "on_behalf_of": self.supervisor_id, "session_id": session_id, "user": sub,
                "reason": "A2A hop must propagate the original human's identity (fail-closed)",
            })
            res = GatewayResult("DENY", req.tool, aid, reason="no human identity on A2A hop")
            return A2AResult(session_id, self.supervisor_id, req.specialist_id, aid, res)

        # 1+3. Record the A2A dispatch (lineage: which supervisor, which session).
        dispatch_aid = self.gateway.audit.record({
            "decision": "A2A_DISPATCH", "tool": req.tool, "agent_id": req.specialist_id,
            "on_behalf_of": self.supervisor_id, "session_id": session_id,
            "user": sub, "task": req.task,
        })

        # 2+4. The specialist's tool call goes through the SAME gateway, authorized
        # as the human (identity propagation) — least-privilege + human-gate intact.
        result = self.gateway.invoke(
            user_claims=req.user_claims,        # the human, never the supervisor
            agent_id=req.specialist_id,
            tool=req.tool,
            args=req.args,
            approval=req.approval,
            raise_on_deny=raise_on_deny,
        )
        return A2AResult(session_id, self.supervisor_id, req.specialist_id, dispatch_aid, result)

    def audit_records(self) -> List[Dict[str, Any]]:
        return self.gateway.audit.records
