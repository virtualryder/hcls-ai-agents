"""
Bound human-approval tokens — tamper-evident, single-use, separation-of-duties.

A high-risk (write) tool call may execute only when a *bound* approval token is
present. The token is minted server-side by an entitled human reviewer and is
cryptographically bound to **requestor + agent + tool + a hash of the exact args**,
so it cannot be:

  * forged           — HMAC signature over the bound fields (reviewer never holds the key)
  * self-approved    — mint rejects approver == requestor (separation of duties)
  * retargeted       — verify rejects a token whose tool/agent/requestor differs
  * tampered         — verify rejects if the args changed after approval (args_hash mismatch)
  * replayed         — each token's jti is single-use (claimed on first successful verify)

This is the reference model for Amazon Bedrock AgentCore Identity / a Cognito-authorized
reviewer service minting an STS-scoped, request-bound approval. The legally consequential
*commit* itself is additionally withheld from every agent grant (see policy.CONSEQUENTIAL_COMMITS).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, Optional

_SECRET = os.getenv("APPROVAL_TOKEN_SECRET", secrets.token_hex(32)).encode()
_TTL_SECONDS = int(os.getenv("APPROVAL_TOKEN_TTL", "900"))  # 15 min default
_USED_JTIS: set[str] = set()  # in-process fallback (demo/test only)


# ── Durable single-use registry ──────────────────────────────────────────────
# Replay protection MUST survive cold starts, separate Lambda environments, and
# horizontal scaling. When APPROVAL_CONSUMPTION_TABLE is set, each token's jti is
# claimed by an ATOMIC conditional create (attribute_not_exists(jti)) in DynamoDB
# before the approved action runs — a second environment presenting the same token
# loses the conditional write and is rejected. The in-memory set is a demo-only
# fallback used when no table is configured. The two indirections below are kept
# small so they can be swapped in tests without faking the AWS SDK.
def _ddb_claim(table: str, jti: str) -> bool:
    """Atomically claim a jti. Returns True if newly claimed, False if already used."""
    import datetime
    import boto3
    from botocore.exceptions import ClientError

    ttl = int(time.time()) + max(_TTL_SECONDS * 4, 3600)
    try:
        boto3.client("dynamodb").put_item(
            TableName=table,
            Item={
                "jti": {"S": jti},
                "claimed_at": {"S": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                "ttl": {"N": str(ttl)},
            },
            ConditionExpression="attribute_not_exists(jti)",
        )
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return False
        raise


def _ddb_exists(table: str, jti: str) -> bool:
    """Non-consuming existence check (for verify(consume=False))."""
    import boto3
    resp = boto3.client("dynamodb").get_item(
        TableName=table, Key={"jti": {"S": jti}}, ConsistentRead=True
    )
    return "Item" in resp


def _consume_jti(jti: str, *, consume: bool) -> None:
    """Enforce single-use. Raises ApprovalInvalid on replay. Durable when a table is set."""
    if not jti:
        raise ApprovalInvalid("approval token missing jti")
    table = os.getenv("APPROVAL_CONSUMPTION_TABLE")
    if table:
        if consume:
            if not _ddb_claim(table, jti):
                raise ApprovalInvalid("approval token already used (replay)")
        elif _ddb_exists(table, jti):
            raise ApprovalInvalid("approval token already used (replay)")
        return
    # Demo/test fallback (single process, non-durable).
    if jti in _USED_JTIS:
        raise ApprovalInvalid("approval token already used (replay)")
    if consume:
        _USED_JTIS.add(jti)


class ApprovalInvalid(Exception):
    """The approval token is missing, malformed, self-approved, retargeted, tampered, or replayed."""


def args_hash(args: Optional[Dict[str, Any]]) -> str:
    body = json.dumps(args or {}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _sign(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = hmac.new(_SECRET, body, hashlib.sha256).hexdigest()
    return f"{body.decode()}.{sig}"


def mint_approval_token(*, requestor: str, agent_id: str, tool: str,
                        args: Optional[Dict[str, Any]], approver: str) -> str:
    """Mint a bound approval token. Raises ApprovalInvalid on self-approval (separation of duties)."""
    if not approver or not requestor:
        raise ApprovalInvalid("requestor and approver are both required")
    if approver == requestor:
        raise ApprovalInvalid("self-approval is forbidden (separation of duties)")
    payload = {
        "jti": str(uuid.uuid4()),
        "requestor": requestor,
        "approver": approver,
        "agent_id": agent_id,
        "tool": tool,
        "args_hash": args_hash(args),
        "iat": int(time.time()),
        "exp": int(time.time()) + _TTL_SECONDS,
    }
    return _sign(payload)


def verify_approval_token(token: str, *, requestor: str, agent_id: str, tool: str,
                          args: Optional[Dict[str, Any]], consume: bool = True) -> Dict[str, Any]:
    """Verify a bound approval token. Raises ApprovalInvalid on any binding failure.

    On success returns the decoded payload; if consume=True the jti is marked used
    (single-use) so a replay of the same token is rejected.
    """
    try:
        body, sig = token.rsplit(".", 1)
        expected = hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ApprovalInvalid("bad signature")
        payload = json.loads(body)
    except ApprovalInvalid:
        raise
    except Exception as exc:  # malformed
        raise ApprovalInvalid(f"malformed approval token: {exc}") from exc

    if int(time.time()) > int(payload.get("exp", 0)):
        raise ApprovalInvalid("approval token expired")
    if payload.get("approver") == payload.get("requestor"):
        raise ApprovalInvalid("self-approval is forbidden (separation of duties)")
    if payload.get("requestor") != requestor:
        raise ApprovalInvalid("requestor mismatch")
    if payload.get("agent_id") != agent_id:
        raise ApprovalInvalid("agent mismatch (token retargeted)")
    if payload.get("tool") != tool:
        raise ApprovalInvalid("tool mismatch (token retargeted)")
    if payload.get("args_hash") != args_hash(args):
        raise ApprovalInvalid("args changed after approval (tamper)")
    _consume_jti(payload.get("jti"), consume=consume)
    return payload


def is_bound_approval(approval: Optional[Dict[str, Any]]) -> bool:
    """True if the approval carries a bound token (vs. the legacy unbound reviewer dict)."""
    return bool(approval and isinstance(approval, dict) and approval.get("token"))
