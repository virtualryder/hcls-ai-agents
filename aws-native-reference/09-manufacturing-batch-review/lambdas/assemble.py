"""Assemble Lambda — load the batch record + LIMS results and scan by exception.

In production the MES/LIMS reads flow through the connector behind the gateway;
here the input carries the record (or a fixture) so the pipeline is testable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import audit, ok
import core


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    state = dict(body)
    state.setdefault("revision_count", 0)
    rec = state.get("raw_batch_record", {}) or {}
    scan = core.scan(rec, state.get("lims_results", []) or [])
    state["exceptions"] = scan["exceptions"]
    state["exception_count"] = scan["exception_count"]
    state["critical_count"] = scan["critical_count"]
    state["has_open_exceptions"] = scan["exception_count"] > 0
    state["right_first_time"] = scan["exception_count"] == 0
    state["product"] = state.get("product") or rec.get("product", "UNKNOWN-PRODUCT")
    state.setdefault("audit_trail", []).append(
        audit("assemble", {"batch_id": state.get("batch_id"),
                           "exception_count": scan["exception_count"],
                           "critical_count": scan["critical_count"]}))
    return ok(state)
