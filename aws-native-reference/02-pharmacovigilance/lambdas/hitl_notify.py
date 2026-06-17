"""
HITL Notify Lambda — persist the task token and notify the PV Medical Reviewer.

Invoked by Step Functions via waitForTaskToken.  The state machine PAUSES here
until a qualified reviewer calls SendTaskSuccess (approve) or SendTaskFailure
(reject) with the task token.  This is the framework-enforced human gate:
no code path submits an ICSR without it.

In demo mode (no HITL_TOPIC_ARN / REVIEW_TABLE set) the record is logged locally.
In production:
  - The task token + case summary is written to DynamoDB (REVIEW_TABLE)
  - An SNS notification is published to the PV reviewer queue (HITL_TOPIC_ARN)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from _shared import audit, ok

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REVIEW_TABLE = os.environ.get("REVIEW_TABLE", "")
HITL_TOPIC_ARN = os.environ.get("HITL_TOPIC_ARN", "")


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Step Functions passes:
      event = {
        "input": <full case_state>,
        "task_token": "$$.Task.Token"
      }
    """
    task_token = event.get("task_token", event.get("taskToken", "DEMO_TOKEN"))
    payload = event.get("input", event)
    if isinstance(payload, str):
        payload = json.loads(payload)

    case_id = payload.get("case_id", "UNKNOWN")
    routing = payload.get("routing", {})
    action = routing.get("action", "UNKNOWN")
    is_serious = payload.get("is_serious", False)
    clock = payload.get("reporting_clock_days")
    meddra_pt = payload.get("meddra_pt", "")

    record = {
        "task_token": task_token,
        "case_id": case_id,
        "action": action,
        "is_serious": is_serious,
        "reporting_clock_days": clock,
        "meddra_pt": meddra_pt,
        "narrative_preview": (payload.get("narrative_text") or "")[:300],
        "phi_findings": routing.get("phi_findings", []),
        "grounding_findings": routing.get("grounding_findings", []),
        "missing_elements": routing.get("missing_elements", []),
    }

    # DynamoDB persistence (production)
    if REVIEW_TABLE:  # pragma: no cover
        try:
            import boto3

            boto3.client("dynamodb").put_item(
                TableName=REVIEW_TABLE,
                Item={
                    "case_id": {"S": str(case_id)},
                    "payload": {"S": json.dumps(record)},
                },
            )
        except Exception as exc:
            logger.warning("DynamoDB put_item failed: %s", exc)

    # SNS notification (production)
    message = {
        "subject": f"[PV] ICSR medical review required — {case_id}",
        "case_id": case_id,
        "action": action,
        "is_serious": is_serious,
        "reporting_clock_days": clock,
        "meddra_pt": meddra_pt,
        "task_token": task_token,
        "approve_payload": {"taskToken": task_token, "decision": "approved"},
        "reject_payload": {"taskToken": task_token, "decision": "rejected"},
    }

    if HITL_TOPIC_ARN:  # pragma: no cover
        try:
            import boto3

            boto3.client("sns").publish(
                TopicArn=HITL_TOPIC_ARN,
                Subject=message["subject"],
                Message=json.dumps(message, indent=2),
            )
            logger.info("SNS notification sent for %s", case_id)
        except Exception as exc:
            logger.warning("SNS publish failed (demo fallback): %s", exc)
    else:
        logger.info("[DEMO] HITL notification: %s", json.dumps(message, indent=2))

    # Audit
    audit_trail = payload.get("audit_trail", [])
    trail_entry = audit(
        "hitl_notify",
        {
            "case_id": case_id,
            "action": action,
            "task_token_present": bool(task_token),
            "is_serious": is_serious,
            "reporting_clock_days": clock,
        },
    )
    audit_trail = list(audit_trail) + [trail_entry]

    # Return is ignored by SFN while waiting for task token callback.
    return ok(
        {
            "queued_for_review": True,
            "case_id": case_id,
            "audit_trail": audit_trail,
        }
    )
