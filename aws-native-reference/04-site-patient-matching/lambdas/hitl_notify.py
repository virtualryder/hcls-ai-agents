"""HITL Notify Lambda — SNS notification for site selection lead review."""
from __future__ import annotations
import json, logging, os
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
    tier = evidence.get("feasibility_score", {}).get("tier", "UNKNOWN")
    n_flags = len(evidence.get("fairness_flags", []))

    message = {
        "subject": f"[SiteMatch] Site ranking review required --- {study_id}",
        "study_id": study_id,
        "action": action,
        "feasibility_tier": tier,
        "fairness_flags": n_flags,
        "task_token": task_token,
        "approve_payload": {"taskToken": task_token, "decision": "APPROVE_RANKING"},
        "reject_payload": {"taskToken": task_token, "decision": "REVISE"},
    }

    if SNS_TOPIC_ARN:
        try:
            import boto3
            boto3.client("sns").publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=message["subject"],
                Message=json.dumps(message, indent=2),
            )
        except Exception as exc:
            logger.warning("SNS publish failed: %s", exc)
    else:
        logger.info("[DEMO] HITL notification: %s", json.dumps(message, indent=2))

    trail_entry = audit("hitl_notify", {
        "study_id": study_id, "action": action,
        "task_token_present": bool(task_token),
    })

    return ok({
        "evidence": evidence,
        "routing": routing,
        "task_token": task_token,
        "audit_trail": audit_trail + [trail_entry],
    })
