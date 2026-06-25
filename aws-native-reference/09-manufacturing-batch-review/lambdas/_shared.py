"""Shared helpers for the Pharmacovigilance native Lambda functions."""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def audit(event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Build a GVP Module VI / 21 CFR Part 11 compliant audit entry."""
    return {
        "event_type": event_type,
        "timestamp": now(),
        "actor": "ai_agent",
        **details,
    }


def ok(body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard Lambda response shape for Step Functions payload passthrough."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def err(status: int, msg: str) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}),
    }
