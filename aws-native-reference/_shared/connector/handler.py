"""
Shared connector Lambda — the backend behind every MCP gateway *target*.

One deployed copy of this handler stands behind each system-of-record target
(rim, dms, safety, edc, ctms, etmf, rwd, qms, crm, ...). It is invoked by:

  * **AgentCore Gateway** mode — Bedrock AgentCore Gateway routes an MCP tool
    call to this Lambda (TargetConfiguration.Mcp.Lambda).
  * **Portable** mode — API Gateway (HTTP API) with a Cognito JWT Lambda
    authorizer proxies the same MCP tool call to this Lambda.

Either way the contract is identical and the enforcement is identical: the call
is run through ``platform_core``'s ``MCPGateway`` so the **deny-by-default,
least-privilege intersection, human-approval gate, scoped-token, and PHI-masked
append-only audit** semantics are exactly the tested Python reference — not a
re-implementation that can drift. The connector Lambda therefore *is* the
governed front door; no agent ever calls a vendor system directly.

Environment:
  CONNECTOR_KIND   the system this target fronts (rim|dms|safety|...). The tool
                   in the request must belong to this kind, or the call is denied.
  CONNECTOR_MODE   fixture (default, deterministic) | live (real vendor API).
  AUDIT_TABLE      DynamoDB table for the append-only audit mirror (optional).
  ENVIRONMENT      dev|test|prod (prod tightens posture).

Request payload (normalized from either gateway):
  {
    "tool": "safety.search_duplicates",     # required, "<kind>.<operation>"
    "arguments": { ... },                     # tool arguments
    "agent_id": "02-pharmacovigilance",      # which agent is acting
    "identity": { "sub": "...", "custom:hcls_role": "PV_MEDICAL_REVIEWER" },
    "approval": { "approved": true, "reviewer": {"sub": "..."} }   # high-risk only
  }

Response:
  { "decision": "ALLOW|DENY|PENDING_APPROVAL", "tool": "...", "audit_id": "...",
    "result": <connector result | null>, "reason": "..." }
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from hcls_agent_platform.mcp_gateway.gateway import MCPGateway

# One gateway instance per warm container (cheap; holds no per-request state).
_GATEWAY = MCPGateway()


# ── event normalization ──────────────────────────────────────────────────────
def _normalize(event: Dict[str, Any]) -> Dict[str, Any]:
    """Accept AgentCore-Gateway, API-Gateway-proxy, or direct-invoke shapes."""
    # API Gateway (HTTP API) proxy integration: the MCP body is a JSON string.
    # Preserve requestContext so the JWT authorizer claims survive normalization.
    if isinstance(event, dict) and "body" in event and "tool" not in event:
        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64

            body = base64.b64decode(body).decode("utf-8")
        request_context = event.get("requestContext")
        try:
            event = json.loads(body)
        except (TypeError, ValueError):
            event = {}
        if isinstance(event, dict) and request_context is not None:
            event.setdefault("requestContext", request_context)
    # AgentCore Gateway nests the MCP call under "input"/"invocationInput".
    for key in ("input", "invocationInput", "request"):
        if isinstance(event, dict) and key in event and "tool" not in event:
            inner = event[key]
            if isinstance(inner, str):
                try:
                    inner = json.loads(inner)
                except (TypeError, ValueError):
                    inner = {}
            if isinstance(inner, dict):
                event = inner
            break
    return event if isinstance(event, dict) else {}


def _claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """Verified IdP claims. Prefer the API-Gateway/AgentCore authorizer context."""
    for key in ("identity", "claims", "userClaims"):
        val = event.get(key)
        if isinstance(val, dict) and val:
            return val
    # API Gateway JWT authorizer surfaces claims here.
    rc = event.get("requestContext") or {}
    authz = (rc.get("authorizer") or {}).get("jwt", {}).get("claims")
    if isinstance(authz, dict) and authz:
        return authz
    return {}


def _audit_to_dynamo(result: Any) -> None:
    """Best-effort mirror of the audit entry into the append-only DynamoDB table."""
    table = os.getenv("AUDIT_TABLE")
    if not table:
        return
    try:  # pragma: no cover - requires AWS
        import datetime

        import boto3

        boto3.client("dynamodb").put_item(
            TableName=table,
            Item={
                "audit_id": {"S": str(result.audit_id)},
                "ts": {"S": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                "decision": {"S": result.decision},
                "tool": {"S": result.tool},
            },
        )
    except Exception:  # never fail the call because the mirror failed
        pass


# ── Lambda entry point ───────────────────────────────────────────────────────
def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    event = _normalize(event)
    tool = event.get("tool") or event.get("name") or ""
    kind = os.getenv("CONNECTOR_KIND", "")

    # Defense in depth: a target may only serve its own connector kind.
    if kind and tool and not tool.startswith(f"{kind}."):
        return {
            "decision": "DENY",
            "tool": tool,
            "audit_id": "",
            "result": None,
            "reason": f"tool '{tool}' not served by the '{kind}' target",
        }

    result = _GATEWAY.invoke(
        user_claims=_claims(event),
        agent_id=event.get("agent_id", ""),
        tool=tool,
        args=event.get("arguments") or event.get("args") or {},
        approval=event.get("approval"),
    )
    _audit_to_dynamo(result)

    return {
        "decision": result.decision,
        "tool": result.tool,
        "audit_id": result.audit_id,
        "allowed": result.allowed,
        "result": result.result,
        "reason": result.reason,
        "requires_approval": result.requires_approval,
        "scope": result.scope,
    }
