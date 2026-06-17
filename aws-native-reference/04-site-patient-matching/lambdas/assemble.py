"""Assemble Lambda — gathers RWD cohort results and CTMS site data."""
from __future__ import annotations
import json, sys
from typing import Any, Dict
from _shared import audit, ok

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    study_id = event.get("study_id", "UNKNOWN")
    protocol_id = event.get("protocol_id", "UNKNOWN")
    indication = event.get("indication", "")
    target = int(event.get("target_enrollment", 0))
    eligibility_criteria = event.get("eligibility_criteria", {})
    cohort_results = event.get("cohort_results", {
        "total_eligible": 0, "sites_with_data": 0, "site_counts": [],
        "phi_note": "All counts are aggregate and de-identified per 45 CFR 164.514.",
    })

    evidence = {
        "study_id": study_id,
        "protocol_id": protocol_id,
        "indication": indication,
        "target_enrollment": target,
        "eligibility_criteria": eligibility_criteria,
        "cohort_results": cohort_results,
    }

    trail_entry = audit("assemble", {
        "study_id": study_id,
        "total_eligible": cohort_results.get("total_eligible"),
        "target_enrollment": target,
    })

    return ok({
        "evidence": evidence,
        "audit_trail": [trail_entry],
        "revision_count": 0,
        "revision_notes": "",
    })
