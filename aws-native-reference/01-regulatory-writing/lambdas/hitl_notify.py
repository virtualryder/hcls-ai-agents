"""
HITL notify: persist the task token and notify the Regulatory Approver.

Invoked by Step Functions via waitForTaskToken. It stores {task_token, draft,
findings} for the review UI and returns nothing — the state machine PAUSES here
until a human calls SendTaskSuccess (approve) or SendTaskFailure (reject) with
their verified identity. This is the framework-enforced human gate; no code path
finalizes a submission without it.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    task_token = event.get("task_token")
    payload = event.get("input", {})
    record = {
        "task_token": task_token,
        "request_id": payload.get("request_id"),
        "draft": payload.get("draft"),
        "compliance_findings": payload.get("compliance_findings", []),
        "grounding_findings": payload.get("grounding_findings", []),
        "action": payload.get("routing", {}).get("action"),
    }
    table = os.getenv("REVIEW_TABLE")
    if table:  # pragma: no cover - requires AWS
        import boto3

        boto3.client("dynamodb").put_item(
            TableName=table,
            Item={"request_id": {"S": str(record["request_id"])},
                  "payload": {"S": json.dumps(record)}},
        )
    # SNS/EventBridge notification would fire here. Return is ignored by SFN.
    return {"queued_for_review": True, "request_id": record["request_id"]}
