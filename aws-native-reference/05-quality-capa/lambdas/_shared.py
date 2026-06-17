"""Shared helpers for the Quality CAPA native Lambdas."""
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def audit(state: Dict[str, Any], action: str, node: str) -> Dict[str, Any]:
    entry = {"timestamp": now(), "actor": "ai_agent", "action": action, "node": node}
    state.setdefault("audit_trail", []).append(entry)
    return state


def ok(state: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda return shape for Step Functions (payload passthrough)."""
    return state
