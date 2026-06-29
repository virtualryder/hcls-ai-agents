"""
Outbox reconciliation (round-2 #4).

The connector writes an immutable INTENT record before a consequential action and a
COMMITTED record after the system-of-record responds. A crash in between leaves an
INTENT with no matching COMMITTED. This job scans the audit table for such orphans so
an operator can confirm with the system of record and either complete or compensate.

Run on a schedule (EventBridge → Lambda) pointed at AUDIT_TABLE. Read-only: it reports;
a human resolves. Records are keyed `<idempotency_key>#intent` and `<result_audit_id>`
sharing the same `idempotency_key`, so an orphan = an INTENT whose idempotency_key has
no COMMITTED row.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List


def find_orphans(scan_pages: Any) -> List[Dict[str, str]]:
    """Pure core: given an iterable of DynamoDB items, return INTENT rows whose
    idempotency_key has no COMMITTED row. `scan_pages` is an iterable of items
    (each a plain dict of {field: value}). Kept dependency-free for unit testing."""
    committed = set()
    intents: Dict[str, Dict[str, str]] = {}
    for it in scan_pages:
        idem = it.get("idempotency_key", "")
        if it.get("status") == "COMMITTED":
            committed.add(idem)
        elif it.get("status") == "INTENT":
            intents[idem] = it
    return [v for k, v in intents.items() if k not in committed]


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:  # pragma: no cover - requires AWS
    import boto3

    table = os.environ["AUDIT_TABLE"]
    ddb = boto3.client("dynamodb")
    items: List[Dict[str, str]] = []
    kwargs: Dict[str, Any] = {"TableName": table}
    while True:
        resp = ddb.scan(**kwargs)
        for raw in resp.get("Items", []):
            items.append({k: list(v.values())[0] for k, v in raw.items()})
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    orphans = find_orphans(items)
    return {"orphan_count": len(orphans),
            "orphans": [{"idempotency_key": o.get("idempotency_key"),
                         "tool": o.get("tool"), "ts": o.get("ts")} for o in orphans]}
