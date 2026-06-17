"""
Authentication & reviewer identity — federated IdP claims for HCLS roles.

The suite never manages its own user accounts. Identity federates from the
customer's IdP (Okta/Entra/Active Directory) via Amazon Cognito (or Amazon
Bedrock AgentCore Identity), and roles derive from IdP group membership:

    GRP-REG-AUTHORS      -> REGULATORY_AUTHOR
    GRP-REG-APPROVERS    -> REGULATORY_APPROVER
    GRP-PV-PROCESSORS    -> PV_PROCESSOR
    GRP-PV-PHYSICIANS    -> PV_MEDICAL_REVIEWER     (signs SAE/ICSR assessments)
    GRP-CLINOPS          -> CLINOPS_LEAD
    GRP-QUALITY          -> QUALITY_REVIEWER
    GRP-QP               -> QUALIFIED_PERSON         (batch/CAPA approval)
    GRP-MSL              -> MSL
    GRP-MEDICAL-AFFAIRS  -> MEDICAL_AFFAIRS_APPROVER

verify_jwt validates the token (signature/exp/aud) when PyJWT + a JWKS URL are
configured; in dev it accepts a pre-decoded claims dict so the demo runs without
an IdP. require_role enforces role membership for HITL approval steps, and
record_reviewer_identity binds a verified human identity into an approval record
(21 CFR Part 11 electronic-signature linkage).
"""
from __future__ import annotations

import datetime as _dt
import logging
import os
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

ROLE_CLAIM = os.getenv("AUTH_ROLE_CLAIM", "custom:hcls_role")


class AuthError(Exception):
    """Raised on authentication / authorization failure (fail-closed)."""


def roles_from_claims(claims: Dict[str, Any]) -> List[str]:
    raw = claims.get(ROLE_CLAIM) or claims.get("roles") or claims.get("cognito:groups") or []
    if isinstance(raw, str):
        return [r.strip() for r in raw.split(",") if r.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(r) for r in raw]
    return []


def verify_jwt(token_or_claims: Any) -> Dict[str, Any]:
    """
    Verify a bearer token and return its claims.

    Production: validates RS256 signature against AUTH_JWKS_URL with audience
    AUTH_AUDIENCE. Dev: if given a dict, treats it as already-verified claims so
    the local demo runs without an IdP. Fails closed (raises AuthError).
    """
    if isinstance(token_or_claims, dict):
        if not token_or_claims.get("sub"):
            raise AuthError("claims missing 'sub' (fail-closed)")
        return token_or_claims

    jwks_url = os.getenv("AUTH_JWKS_URL")
    if not jwks_url:
        raise AuthError("AUTH_JWKS_URL not configured; cannot verify token")
    try:  # pragma: no cover - requires network/IdP
        import jwt
        from jwt import PyJWKClient

        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token_or_claims)
        claims = jwt.decode(
            token_or_claims,
            signing_key.key,
            algorithms=["RS256"],
            audience=os.getenv("AUTH_AUDIENCE"),
        )
        if not claims.get("sub"):
            raise AuthError("verified token missing 'sub'")
        return claims
    except AuthError:
        raise
    except Exception as exc:  # pragma: no cover
        raise AuthError(f"token verification failed: {exc}") from exc


def require_role(claims: Dict[str, Any], allowed: Iterable[str]) -> str:
    """Return the first matching role, or raise AuthError. Used at HITL gates."""
    user_roles = set(roles_from_claims(claims))
    allowed_set = set(allowed)
    match = user_roles & allowed_set
    if not match:
        raise AuthError(
            f"user roles {sorted(user_roles)} lack any required role {sorted(allowed_set)}"
        )
    return sorted(match)[0]


def record_reviewer_identity(claims: Dict[str, Any], decision: str, meaning: str) -> Dict[str, Any]:
    """
    Build a Part 11-style electronic-signature record bound to a verified human.

    meaning is the signature meaning (e.g., "Approved SAE causality assessment",
    "Authorized CAPA closure"). The record is attached to the audit trail.
    """
    sub = claims.get("sub")
    if not sub:
        raise AuthError("cannot record reviewer identity without verified subject")
    return {
        "reviewer": {
            "sub": sub,
            "name": claims.get("name") or claims.get("email") or sub,
            "roles": roles_from_claims(claims),
        },
        "decision": decision,
        "signature_meaning": meaning,
        "signed_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "approved": decision.lower() in ("approve", "approved", "sign", "signed", "authorize"),
    }
