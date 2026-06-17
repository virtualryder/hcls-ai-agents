"""
HITL notify: persist the task token and notify the Medical Affairs Approver.

Invoked by Step Functions via waitForTaskToken. The state machine PAUSES here
until the Approver calls SendTaskSuccess (approve) or SendTaskFailure (reject).
This is the framework-enforced HITL gate for HIGH-RISK MLR submission.
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
        "brief": payload.get("brief"),
        "compliance_findings": payload.get("compliance_findings", []),
        "grounding_findings": payload.get("grounding_findings", []),
        "action": payload.get("routing", {}).get("action"),
        "hcp_id": payload.get("hcp_id"),
    }
    table = os.getenv("REVIEW_TABLE")
    if table:  # pragma: no cover - requires AWS
        import boto3
        boto3.client("dynamodb").put_item(
            TableName=table,
            Item={
                "request_id": {"S": str(record["request_id"])},
                "payload": {"S": json.dumps(record)},
            },
        )
    return {"queued_for_review": True, "request_id": record["request_id"]}
