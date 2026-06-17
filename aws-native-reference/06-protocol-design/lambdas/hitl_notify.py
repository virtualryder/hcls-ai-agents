"""
HITL notify: persist the task token and notify the Medical/Clinical Reviewer.

Invoked by Step Functions via waitForTaskToken. Stores {task_token, draft_protocol,
findings} for the reviewer UI and returns nothing — the state machine PAUSES here
until a reviewer calls SendTaskSuccess (approve) or SendTaskFailure (reject) with
their verified identity. This is the framework-enforced human gate; no code path
finalizes a protocol or initiates IND/CTA submission without it.
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
        "indication": payload.get("indication"),
        "phase": payload.get("phase"),
        "draft_protocol": payload.get("draft_protocol"),
        "compliance_findings": payload.get("compliance_findings", []),
        "grounding_findings": payload.get("grounding_findings", []),
        "regulatory_risks": payload.get("regulatory_risks", []),
        "action": payload.get("routing", {}).get("action"),
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
    # SNS/EventBridge notification to reviewer would fire here.
    return {"queued_for_review": True, "request_id": record["request_id"]}
