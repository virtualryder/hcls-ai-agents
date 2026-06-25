"""Finalize Lambda — record the QA disposition AFTER the waitForTaskToken approval.

The review payload (from the QA gate) carries the verified reviewer identity and
the decision (RELEASE/HOLD). Without an approved review, status is PENDING.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import audit, ok


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    review = event.get("review", {}) or {}
    state = dict(body)
    approved = bool(review.get("approved"))
    decision = review.get("decision") or state.get("disposition_recommendation")
    if approved:
        state["disposition_id"] = review.get("disposition_id", "DISP-0001")
        state["batch_status"] = "RELEASED" if decision == "RELEASE" else "HELD"
    else:
        state["batch_status"] = "PENDING"
    state.setdefault("audit_trail", []).append(
        audit("finalize", {"batch_id": state.get("batch_id"), "status": state["batch_status"],
                           "actor": review.get("reviewer", "system"),
                           "human_review_required": True}))
    return ok(state)
