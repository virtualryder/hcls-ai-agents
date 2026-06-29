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
    """Resolve the caller's verified identity/role.

    SECURITY (F3): for any network-originated request, identity MUST come from the
    authenticated authorizer context — never from the request body, which the caller
    controls and could use to assert a more privileged role. We therefore read the
    JWT authorizer claims FIRST. Body-supplied identity keys ("identity"/"claims"/
    "userClaims") are honored only in explicit local-test mode (HCLS_LOCAL_TEST=1),
    so unit tests and fixture runs can inject a subject without a real IdP.
    """
    # 1) Authenticated API Gateway / AgentCore JWT authorizer claims (authoritative).
    rc = event.get("requestContext") or {}
    authz = (rc.get("authorizer") or {}).get("jwt", {}).get("claims")
    if isinstance(authz, dict) and authz:
        return authz
    # 2) Body-supplied identity is accepted only for a genuine DIRECT invoke (no
    #    requestContext present) — i.e. an IAM-authenticated internal caller such as
    #    the finalize Lambda committing on the approver's authority — or in explicit
    #    local-test mode. A network request always carries requestContext, so this
    #    branch is unreachable from the API and the F3 protection still holds there.
    direct_invoke = "requestContext" not in event
    if direct_invoke or os.getenv("HCLS_LOCAL_TEST") == "1":
        for key in ("identity", "claims", "userClaims"):
            val = event.get(key)
            if isinstance(val, dict) and val:
                return val
    return {}


import hashlib
import datetime


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _args_hash(args: Dict[str, Any]) -> str:
    body = json.dumps(args or {}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _idempotency_key(agent_id: str, tool: str, args: Dict[str, Any], approval: Any) -> str:
    """Stable key for an action: same agent+tool+args+approval-jti = same logical action.
    Lets a retried invocation be de-duplicated by the connector / system of record."""
    jti = ""
    if isinstance(approval, dict):
        tok = approval.get("token") or ""
        # the jti is embedded in the signed token body (json.sig)
        try:
            jti = json.loads(tok.rsplit(".", 1)[0]).get("jti", "") if tok else ""
        except Exception:
            jti = ""
    seed = f"{agent_id}|{tool}|{_args_hash(args)}|{jti}"
    return hashlib.sha256(seed.encode()).hexdigest()


def _approval_meta(approval: Any) -> Dict[str, str]:
    if not isinstance(approval, dict):
        return {"approval_jti": "", "approver": ""}
    tok = approval.get("token") or ""
    jti = ""
    try:
        jti = json.loads(tok.rsplit(".", 1)[0]).get("jti", "") if tok else ""
    except Exception:
        jti = ""
    reviewer = approval.get("reviewer") or {}
    approver = reviewer.get("sub", "") if isinstance(reviewer, dict) else str(reviewer)
    return {"approval_jti": jti, "approver": approver}


def _evidence(*, audit_id, status, idem, claims, agent_id, tool, args, approval,
              decision, allowed, reason, scope, lineage=None, response=None) -> Dict[str, Any]:
    """The COMPLETE 21 CFR Part 11-relevant audit record (round-2 #4).

    Contains identity, agent, tool, canonical args hash, approval id + reviewer,
    model + prompt version, system-of-record lineage and response, decision/scope —
    not a four-field summary."""
    item = {
        "audit_id": {"S": str(audit_id)},
        "idempotency_key": {"S": str(idem)},
        "status": {"S": status},                                # INTENT | COMMITTED
        "ts": {"S": _now()},
        "agent_id": {"S": str(agent_id or "")},
        "tool": {"S": str(tool or "")},
        "user_sub": {"S": str((claims or {}).get("sub", ""))},
        "user_role": {"S": str((claims or {}).get("custom:hcls_role", ""))},
        "args_hash": {"S": _args_hash(args)},
        "decision": {"S": str(decision)},
        "allowed": {"BOOL": bool(allowed)},
        "reason": {"S": str(reason or "")},
        "scope": {"S": json.dumps(scope)},
        "model_version": {"S": os.getenv("MODEL_ID", os.getenv("BEDROCK_MODEL_ID", ""))},
        "prompt_version": {"S": os.getenv("PROMPT_VERSION", "")},
        "connector_mode": {"S": os.getenv("CONNECTOR_MODE", "fixture")},
    }
    item.update(_approval_meta(approval))
    item["approval_jti"] = {"S": item.pop("approval_jti")}
    item["approver"] = {"S": item.pop("approver")}
    if lineage is not None:
        item["lineage"] = {"S": json.dumps(lineage)}
    if response is not None:
        # System-of-record response becomes part of the evidence (truncated).
        item["sor_response"] = {"S": json.dumps(response)[:1500]}
    return item


def _put_immutable(table: str, item: Dict[str, Any]) -> None:
    """Conditional, append-only PutItem. FAIL CLOSED: a non-idempotent failure raises.
    Factored out so tests can substitute an in-memory store."""
    import boto3  # pragma: no cover - requires AWS
    from botocore.exceptions import ClientError  # pragma: no cover

    try:  # pragma: no cover - requires AWS
        boto3.client("dynamodb").put_item(
            TableName=table, Item=item,
            ConditionExpression="attribute_not_exists(audit_id)",
        )
    except ClientError as exc:  # pragma: no cover
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return  # already written — immutable, idempotent: OK
        raise


# ── Lambda entry point ───────────────────────────────────────────────────────
def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    event = _normalize(event)
    tool = event.get("tool") or event.get("name") or ""
    kind = os.getenv("CONNECTOR_KIND", "")
    agent_id = event.get("agent_id", "")
    args = event.get("arguments") or event.get("args") or {}
    approval = event.get("approval")
    claims = _claims(event)
    table = os.getenv("AUDIT_TABLE")
    idem = _idempotency_key(agent_id, tool, args, approval)

    # Defense in depth: a target may only serve its own connector kind.
    if kind and tool and not tool.startswith(f"{kind}."):
        return {"decision": "DENY", "tool": tool, "audit_id": "", "result": None,
                "reason": f"tool '{tool}' not served by the '{kind}' target"}

    # Transaction boundary (round-2 #4): for a CONSEQUENTIAL action (one carrying a
    # human approval) write an immutable INTENT record BEFORE executing, so a crash
    # between execution and the outcome write is detectable by reconciliation. Reads
    # need no intent row.
    consequential = approval is not None
    if table and consequential:
        _put_immutable(table, _evidence(
            audit_id=f"{idem}#intent", status="INTENT", idem=idem, claims=claims,
            agent_id=agent_id, tool=tool, args=args, approval=approval,
            decision="INTENT", allowed=False, reason="action intended; awaiting execution",
            scope=None, lineage={"connector": kind, "method": tool.split(".")[-1] if tool else ""}))

    result = _GATEWAY.invoke(user_claims=claims, agent_id=agent_id, tool=tool,
                             args=args, approval=approval)

    # Immutable OUTCOME record with the system-of-record response. Fail closed.
    if table:
        _put_immutable(table, _evidence(
            audit_id=str(result.audit_id), status="COMMITTED", idem=idem, claims=claims,
            agent_id=agent_id, tool=tool, args=args, approval=approval,
            decision=result.decision, allowed=result.allowed, reason=result.reason,
            scope=getattr(result, "scope", None),
            lineage={"connector": kind, "method": tool.split(".")[-1] if tool else ""},
            response=result.result))

    return {
        "decision": result.decision,
        "tool": result.tool,
        "audit_id": result.audit_id,
        "idempotency_key": idem,
        "allowed": result.allowed,
        "result": result.result,
        "reason": result.reason,
        "requires_approval": result.requires_approval,
        "scope": result.scope,
    }
