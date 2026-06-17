"""
HITL Notify Lambda — sends the human-review task token to the approver
via SNS (or logs it in demo mode).  The Step Functions WaitForTaskToken
state parks here until the approver calls back with success/failure.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from _shared import audit, ok

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SNS_TOPIC_ARN = os.environ.get("HITL_TOPIC_ARN", "")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    task_token = event.get("taskToken", body.get("taskToken", "DEMO_TOKEN"))
    evidence = body.get("evidence", {})
    routing = body.get("routing", {})
    audit_trail = body.get("audit_trail", [])

    study_id = evidence.get("study_id", "UNKNOWN")
    action = routing.get("action", "UNKNOWN")
    tier = evidence.get("risk_score", {}).get("risk_tier", "UNKNOWN")

    message = {
        "subject": f"[ClinOps] Study health review required — {study_id}",
        "study_id": study_id,
        "action": action,
        "risk_tier": tier,
        "task_token": task_token,
        "approve_payload": {"taskToken": task_token, "decision": "APPROVE_BRIEF"},
        "reject_payload": {"taskToken": task_token, "decision": "REVISE"},
    }

    if SNS_TOPIC_ARN:
        try:
            import boto3
            sns = boto3.client("sns")
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=message["subject"],
                Message=json.dumps(message, indent=2),
            )
            logger.info("SNS notification sent for %s", study_id)
        except Exception as exc:  # pragma: no cover
            logger.warning("SNS publish failed (demo fallback): %s", exc)
    else:
        logger.info("[DEMO] HITL notification: %s", json.dumps(message, indent=2))

    trail_entry = audit(
        "hitl_notify",
        {"study_id": study_id, "action": action, "task_token_present": bool(task_token)},
    )

    return ok(
        {
            "evidence": evidence,
            "routing": routing,
            "task_token": task_token,
            "audit_trail": audit_trail + [trail_entry],
        }
    )
