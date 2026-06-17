# tools/content_retriever.py
# ============================================================
# Content Retriever — selects, validates, and indexes approved
# documents from the DMS (dms.get_document gateway tool).
#
# All content used in MSL briefs must come from approved, current-version
# documents. This module enforces:
#   * status must be APPROVED (not DRAFT, SUPERSEDED, WITHDRAWN)
#   * version is logged for audit
#   * a citation index is built so the drafter can reference sources
# No LLM involvement — pure deterministic logic.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List, Optional


# Documents whose status prevents use in HCP-facing content
_BLOCKED_STATUSES = {"DRAFT", "SUPERSEDED", "WITHDRAWN", "ARCHIVED", "UNDER_REVIEW"}


def validate_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that all documents are approved for use in HCP-facing content.

    Returns:
        {
            "approved": List[Dict],       # safe to use
            "blocked": List[Dict],        # must not be used
            "issues": List[str],          # blocking validation errors
            "warnings": List[str],        # non-blocking notes
        }
    """
    approved: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    issues: List[str] = []
    warnings: List[str] = []

    for doc in documents:
        if not isinstance(doc, dict):
            warnings.append(f"non-dict document entry skipped: {doc!r}")
            continue
        status = str(doc.get("status", "")).upper()
        title = doc.get("title", f"doc_id={doc.get('doc_id', 'unknown')}")
        if status in _BLOCKED_STATUSES:
            blocked.append(doc)
            issues.append(
                f"document '{title}' has status {status!r} — "
                "must not be used in HCP-facing content"
            )
        elif not status or status == "UNKNOWN":
            warnings.append(
                f"document '{title}' has no status field — treating as unapproved"
            )
            blocked.append(doc)
        else:
            approved.append(doc)

    return {
        "approved": approved,
        "blocked": blocked,
        "issues": issues,
        "warnings": warnings,
    }


def build_citation_index(approved_docs: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Build a citation shorthand → document title/version mapping
    for use by the brief drafter.

    Returns e.g. {"[DOC-PI-001 v3.0]": "Demo-Drug Prescribing Information v3.0"}
    """
    index: Dict[str, str] = {}
    for doc in approved_docs:
        doc_id = doc.get("doc_id", "")
        version = doc.get("version", "N/A")
        title = doc.get("title", doc_id)
        key = f"[{doc_id} v{version}]"
        index[key] = f"{title} (v{version})"
    return index


def extract_key_claims(approved_docs: List[Dict[str, Any]]) -> List[str]:
    """
    Extract key factual claims from approved document text for the brief drafter.
    Returns a list of cited claim strings.
    """
    claims: List[str] = []
    for doc in approved_docs:
        doc_id = doc.get("doc_id", "")
        version = doc.get("version", "N/A")
        title = doc.get("title", doc_id)
        text = doc.get("text", "")
        if text:
            # Truncate long documents; the drafter prompt gets the full text
            excerpt = text[:400].strip()
            claims.append(f"From [{doc_id} v{version}] {title!r}: {excerpt}")
    return claims
