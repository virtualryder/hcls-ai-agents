"""
Strands drafter — the LLM DRAFTING layer for the MSL native rebuild.

Drafts an on-label, cited pre-call brief from the HCP profile and approved
documents. Demo fallback so the pipeline runs without AWS. Off-label language
in the output is caught by core.py compliance_findings — the LLM is instructed
not to generate it, and the gate enforces this deterministically.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

SYSTEM_PROMPT = (
    "You are a Medical Science Liaison briefing assistant. "
    "Draft pre-call briefs that are strictly on-label, factual, and cited from approved materials only. "
    "NEVER include off-label information, promotional language, or unsubstantiated claims. "
    "Every factual claim must cite the source document by title and version. "
    "A Medical Affairs Approver must review all briefs before use with HCPs."
)


def _bedrock_model():
    from strands.models import BedrockModel

    kwargs: Dict[str, Any] = dict(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6-20260601-v1:0"),
        region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
        temperature=0.0,
    )
    gid = os.getenv("BEDROCK_GUARDRAIL_ID", "")
    if gid:
        kwargs["guardrail_id"] = gid
        kwargs["guardrail_version"] = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")
    return BedrockModel(**kwargs)


def _demo_brief(hcp_profile: Dict[str, Any], approved_docs: List[Dict[str, Any]],
                topic: str, meeting_date: str, meeting_purpose: str) -> str:
    hcp_name = hcp_profile.get("name", "the HCP")
    specialty = hcp_profile.get("specialty", "the relevant specialty")
    interests = hcp_profile.get("clinical_interests", ["clinical outcomes"])
    interests_str = ", ".join(str(i) for i in interests[:3]) if isinstance(interests, list) else str(interests)
    n_docs = len(approved_docs)
    source_ref = approved_docs[0].get("title", "approved labeling") if approved_docs else "approved labeling"

    return (
        "pre-call brief for meeting with " + hcp_name + " on " + meeting_date + ". "
        "meeting purpose: " + meeting_purpose + ".\n\n"
        "hcp background: " + hcp_name + " is a " + specialty + " specialist "
        "with clinical interests in " + interests_str + ".\n\n"
        "key approved data points for this scientific exchange "
        "(" + str(n_docs) + " approved source document(s) reviewed):\n"
        "- efficacy and safety profile per approved labeling for " + topic + ". "
        "(source: " + source_ref + ")\n"
        "- all claims in this brief are grounded in the approved indication and labeling only.\n\n"
        "anticipated questions: for any question outside the approved indication, "
        "direct the physician to the medical information team for a formal response.\n\n"
        "proposed key messages: communicate the approved efficacy and safety profile per labeling. "
        "reference the published data as cited in approved source documents.\n\n"
        "follow-up actions:\n"
        "- log interaction in crm system within the same business day.\n"
        "- send approved references cited in this brief.\n\n"
        "compliance note: this brief reflects approved, on-label content only. "
        "all factual claims cite approved source documents. "
        "a medical affairs approver must review this brief before any hcp interaction."
    )


def draft_brief(
    hcp_profile: Dict[str, Any],
    approved_docs: List[Dict[str, Any]],
    topic: str,
    meeting_date: str,
    meeting_purpose: str,
) -> Dict[str, Any]:
    """Return {brief, drafted_by}."""
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {
            "brief": _demo_brief(hcp_profile, approved_docs, topic, meeting_date, meeting_purpose),
            "drafted_by": "demo-stub",
        }
    try:
        from strands import Agent

        content_block = "\n".join(
            "[" + d.get("title", "doc") + " v" + d.get("version", "N/A") + "]: " + d.get("text", "")
            for d in approved_docs
        )
        prompt = (
            f"Draft an MSL pre-call brief for {hcp_profile.get('name', 'the HCP')} "
            f"on {meeting_date}.\nTopic: {topic}\nPurpose: {meeting_purpose}\n"
            f"HCP profile: {hcp_profile}\n"
            f"Approved content (on-label only):\n{content_block}\n"
            "Requirements: on-label only, cite source for every claim, include compliance note."
        )
        agent = Agent(model=_bedrock_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
        result = agent(prompt)
        text = getattr(result, "message", None) or str(result)
        return {"brief": str(text), "drafted_by": "bedrock"}
    except Exception:
        return {
            "brief": _demo_brief(hcp_profile, approved_docs, topic, meeting_date, meeting_purpose),
            "drafted_by": "demo-stub-fallback",
        }
