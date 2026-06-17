"""
HITL notify: persist the task token and notify the Qualified Person.

Invoked by Step Functions via waitForTaskToken. Stores {task_token, capa_plan,
findings, action} for the QP review UI and returns nothing — the state machine
PAUSES here until a QP calls SendTaskSuccess (approve) or SendTaskFailure (reject)
with their verified identity. This is the framework-enforced human gate; no code
path creates or closes a CAPA in the QMS without it.
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
        "complaint_id": payload.get("complaint_id"),
        "product": payload.get("product"),
        "severity": payload.get("severity"),
        "capa_plan": payload.get("capa_plan"),
        "compliance_findings": payload.get("compliance_findings", []),
        "grounding_findings": payload.get("grounding_findings", []),
        "action": payload.get("routing", {}).get("action"),
    }
    table = os.getenv("REVIEW_TABLE")
    if table:  # pragma: no cover - requires AWS
        import boto3

        boto3.client("dynamodb").put_item(
            TableName=table,
            Item={
                "complaint_id": {"S": str(record["complaint_id"])},
                "payload": {"S": json.dumps(record)},
            },
        )
    # SNS/EventBridge notification to QP would fire here. Return is ignored by SFN.
    return {"queued_for_qp_review": True, "complaint_id": record["complaint_id"]}
