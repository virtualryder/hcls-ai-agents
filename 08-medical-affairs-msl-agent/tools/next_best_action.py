# tools/next_best_action.py
# ============================================================
# Next Best Action — recommends follow-up actions after the
# MSL meeting based on HCP profile, meeting purpose, and
# approved content available.
#
# Deterministic rule-based logic — no LLM. Used to populate the
# follow-up actions section of the brief and the CRM update.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List


def recommend_actions(
    hcp_profile: Dict[str, Any],
    meeting_purpose: str,
    topic: str,
    approved_docs: List[Dict[str, Any]],
    compliance_findings: List[str],
) -> Dict[str, Any]:
    """
    Recommend next best actions based on meeting context.

    Returns:
        {
            "follow_up_actions": List[str],
            "crm_update_required": bool,
            "send_documents": List[str],  # doc titles to send post-meeting
            "escalation_required": bool,
            "escalation_reason": Optional[str],
        }
    """
    actions: List[str] = []
    docs_to_send: List[str] = []
    escalation = False
    escalation_reason = None

    # Always log the interaction
    actions.append(
        "Log interaction in CRM system within the same business day as the meeting."
    )

    # Off-label or promotional compliance issue → escalate
    off_label = any("off-label" in f for f in compliance_findings)
    promotional = any("promotional" in f for f in compliance_findings)
    if off_label or promotional:
        escalation = True
        escalation_reason = (
            "compliance finding (off-label or promotional content) — "
            "do not proceed with HCP interaction until resolved"
        )
        actions.append(
            "ESCALATE: compliance issue detected — brief must not be used until "
            "Medical Affairs Approver resolves the finding."
        )
        return {
            "follow_up_actions": actions,
            "crm_update_required": True,
            "send_documents": [],
            "escalation_required": True,
            "escalation_reason": escalation_reason,
        }

    # Send approved references post-meeting
    for doc in approved_docs:
        if doc.get("status") == "APPROVED":
            docs_to_send.append(doc.get("title", doc.get("doc_id", "unknown")))
            actions.append(
                f"Send approved reference: {doc.get('title', '')} "
                f"(v{doc.get('version', 'N/A')})."
            )

    # Unsolicited data request → route to medical information
    purpose_lower = meeting_purpose.lower()
    if "unsolicited" in purpose_lower:
        actions.append(
            "Confirm that any data shared was provided in direct response to the "
            "HCP's specific unsolicited request. Document the request and response in CRM."
        )

    # KOL → schedule advisory board follow-up
    tier = hcp_profile.get("engagement_tier") or hcp_profile.get("tier", "")
    if "KOL" in tier or "National" in tier:
        actions.append(
            "Schedule follow-up engagement within 90 days. "
            "Consider advisory board participation if relevant program available."
        )

    # Renal / dosing questions → send PI
    if "renal" in topic.lower() or "dosing" in topic.lower():
        actions.append(
            "Confirm renal dosing guidance per approved prescribing information was shared. "
            "Flag any question outside the approved indication for medical information team response."
        )

    return {
        "follow_up_actions": actions,
        "crm_update_required": True,
        "send_documents": docs_to_send,
        "escalation_required": escalation,
        "escalation_reason": escalation_reason,
    }
