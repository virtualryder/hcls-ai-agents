"""Shared helpers for the Site Patient Matching Lambda functions."""
from __future__ import annotations
import datetime, json
from typing import Any, Dict

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def audit(event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    return {"event_type": event_type, "timestamp": now(), **details}

def ok(body: Dict[str, Any]) -> Dict[str, Any]:
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}

def err(status: int, msg: str) -> Dict[str, Any]:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": msg})}
