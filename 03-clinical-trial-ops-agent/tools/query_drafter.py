# tools/query_drafter.py
# ============================================================
# EDC query drafter for the Clinical Trial Ops agent.
#
# Drafts structured EDC data queries for missing CRF fields,
# visit deviations, and protocol non-compliances. These are
# DRAFTED for ClinOps Lead review — no queries are issued until
# a human approves (high-risk write gate in finalize node).
#
# Deterministic — no LLM call, no API key required.
# ============================================================
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def draft_from_missing_fields(
    missing_data_flags: List[Dict[str, Any]],
    study_id: str,
    protocol_id: str,
) -> List[Dict[str, Any]]:
    """
    Draft EDC queries for each missing-data flag.

    Each flag must have: subject_id, site_id, description, severity.
    Returns list of drafted query dicts ready for ClinOps Lead review.
    """
    queries: List[Dict[str, Any]] = []
    for flag in missing_data_flags:
        subject = flag.get("subject_id", "unknown")
        site = flag.get("site_id", "unknown")
        desc = flag.get("description", "missing data")
        severity = flag.get("severity", "MINOR")
        visit = flag.get("visit", "")

        query_text = (
            f"Data query for subject {subject} at site {site}"
            + (f", visit {visit}" if visit else "")
            + f": {desc}. "
            f"Please provide the missing data or confirm the field is not applicable per protocol "
            f"{protocol_id}. Respond within 5 business days per data management plan."
        )

        queries.append({
            "draft_query_id": f"DQ-{study_id}-{subject}-{len(queries) + 1:03d}",
            "study_id": study_id,
            "subject_id": subject,
            "site_id": site,
            "query_text": query_text,
            "severity": severity,
            "status": "DRAFT",
            "created_date": _now_iso(),
            "requires_approval": True,
        })
    return queries


def draft_from_deviation_flags(
    deviation_flags: List[Dict[str, Any]],
    study_id: str,
    protocol_id: str,
) -> List[Dict[str, Any]]:
    """
    Draft EDC queries for protocol deviation flags.

    Each flag must have: subject_id, site_id, description, deviation_type, severity.
    """
    queries: List[Dict[str, Any]] = []
    for flag in deviation_flags:
        subject = flag.get("subject_id", "unknown")
        site = flag.get("site_id", "unknown")
        desc = flag.get("description", "protocol deviation")
        dev_type = flag.get("deviation_type", "PROTOCOL_DEVIATION")
        severity = flag.get("severity", "MAJOR")

        query_text = (
            f"Protocol deviation query for subject {subject} at site {site}: "
            f"{desc} (deviation type: {dev_type}). "
            f"Please provide a protocol deviation report per protocol {protocol_id} section 8 "
            f"and confirm corrective action taken. Respond within 3 business days."
        )

        queries.append({
            "draft_query_id": f"DV-{study_id}-{subject}-{len(queries) + 1:03d}",
            "study_id": study_id,
            "subject_id": subject,
            "site_id": site,
            "query_text": query_text,
            "deviation_type": dev_type,
            "severity": severity,
            "status": "DRAFT",
            "created_date": _now_iso(),
            "requires_approval": True,
        })
    return queries


def summarize_queries(queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a brief summary dict for the briefing / audit trail."""
    if not queries:
        return {"total": 0, "critical": 0, "major": 0, "minor": 0, "sites_affected": []}

    sites: List[str] = list({q.get("site_id", "") for q in queries if q.get("site_id")})
    by_sev = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0}
    for q in queries:
        sev = q.get("severity", "MINOR").upper()
        by_sev[sev] = by_sev.get(sev, 0) + 1

    return {
        "total": len(queries),
        "critical": by_sev.get("CRITICAL", 0),
        "major": by_sev.get("MAJOR", 0),
        "minor": by_sev.get("MINOR", 0),
        "sites_affected": sorted(sites),
    }
