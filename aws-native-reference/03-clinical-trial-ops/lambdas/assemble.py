"""
Assemble Lambda — gathers study data from CTMS and eTMF into the
execution state that will flow through the Step Functions pipeline.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from _shared import audit, ok


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Expects the Step Functions input:
      {
        "study_id": "...",
        "protocol_id": "...",
        "enrolled": 124,
        "target": 200,
        "query_rate": 1.2,
        "tmf_data": { "completeness_pct": 87, "missing_documents": [...] }
      }
    """
    study_id = event.get("study_id", "UNKNOWN")
    protocol_id = event.get("protocol_id", event.get("protocol", "UNKNOWN"))

    # Accept pre-seeded data (demo / test) or real values
    enrolled = int(event.get("enrolled", 0))
    target = int(event.get("target", 1))
    query_rate = float(event.get("query_rate", 0.0))
    tmf_data = event.get(
        "tmf_data",
        {"completeness_pct": 87, "missing_documents": [], "last_reviewed": "unknown"},
    )

    evidence = {
        "study_id": study_id,
        "protocol_id": protocol_id,
        "enrolled": enrolled,
        "target": target,
        "query_rate": query_rate,
        "tmf_data": tmf_data,
    }

    trail_entry = audit(
        "assemble",
        {
            "study_id": study_id,
            "enrolled": enrolled,
            "target": target,
            "tmf_completeness_pct": tmf_data.get("completeness_pct"),
        },
    )

    return ok(
        {
            "evidence": evidence,
            "audit_trail": [trail_entry],
            "revision_count": 0,
            "revision_notes": "",
        }
    )
