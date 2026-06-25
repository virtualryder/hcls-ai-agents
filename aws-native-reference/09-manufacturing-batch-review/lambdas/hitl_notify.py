"""HITL notify Lambda — invoked by Step Functions with waitForTaskToken.

Persists the task token alongside the batch review so a QA reviewer UI can fetch
the pending review and later call SendTaskSuccess with their signed decision.
Demo: just records the token; production writes to DynamoDB + notifies QA (SNS).
"""
from __future__ import annotations

from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    payload = event.get("input", event)
    token = event.get("task_token", "")
    entry = audit("hitl_notify", {"batch_id": payload.get("batch_id"),
                                  "task_token_present": bool(token),
                                  "status": "PENDING_QA"})
    # production: dynamodb.put_item({review, token}); sns.publish(QA topic)
    return ok({"queued": True, "audit": entry})
