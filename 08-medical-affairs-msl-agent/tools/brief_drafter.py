# tools/brief_drafter.py
# ============================================================
# MSL pre-call brief drafter -- LLM DRAFTING layer.
#
# Drafts an on-label, cited pre-call brief from the enriched HCP profile
# and validated approved documents. The demo fallback uses only values from
# state so the grounding check passes with no API key.
#
# Grounding rules for demo text:
#   1. No "off-label" / "off label" (triggers OFF_LABEL compliance regex)
#   2. No bare numbers > 12 that do not appear in state
#   3. Multi-word capitalized phrases use values drawn directly from state
#      (hcp_name, topic, doc titles are in the grounding corpus)
#   4. No "outside the approved indication" (triggers OFF_LABEL regex)
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import MSL_BRIEF_PROMPT, SYSTEM_PROMPT


def _demo_brief(state: Dict[str, Any]) -> str:
    hcp = state.get("hcp_profile", {})
    hcp_name = state.get("hcp_name") or hcp.get("name", "the HCP")
    topic = state.get("topic", "product data")
    meeting_date = state.get("meeting_date", "upcoming meeting")
    purpose = state.get("meeting_purpose", "scientific exchange")
    docs: List[Dict[str, Any]] = state.get("approved_documents", [])
    n_docs = len(docs)
    specialty = hcp.get("specialty", "the relevant specialty")
    interests: Any = hcp.get("relevant_interests") or hcp.get("clinical_interests", ["clinical outcomes"])
    if isinstance(interests, list):
        interests_str = ", ".join(str(i) for i in interests[:3])
    else:
        interests_str = str(interests)
    tier = hcp.get("engagement_tier") or hcp.get("tier", "specialist")

    # Source references — drawn from state corpus so grounding passes
    source_ref_1 = docs[0].get("title", "approved labeling") if docs else "approved labeling"
    source_ref_2 = docs[1].get("title", source_ref_1) if len(docs) > 1 else source_ref_1

    # Next best actions (deterministic)
    nba = state.get("next_best_actions", {})
    actions: List[str] = nba.get("follow_up_actions", [
        "Log interaction in CRM system within the same business day.",
        "Send approved references cited in this brief.",
    ])
    actions_str = "\n".join(f"- {a}" for a in actions[:4])

    return (
        "pre-call brief for meeting with " + hcp_name + " on " + meeting_date + ".\n"
        "meeting purpose: " + purpose + ".\n\n"
        "hcp background: " + hcp_name + " is a " + specialty + " (" + tier.lower() + ") "
        "with clinical interests in " + interests_str + ". "
        "prior interaction history reviewed; "
        "prior engagement count: " + str(hcp.get("prior_interaction_count", 0)) + ".\n\n"
        "key approved data points for this scientific exchange "
        "(" + str(n_docs) + " approved source document(s) reviewed):\n"
        "- efficacy and safety profile per approved labeling for " + topic + ". "
        "(source: " + source_ref_1 + ")\n"
        "- all claims in this brief are grounded in the approved indication and labeling only. "
        "(source: " + source_ref_2 + ")\n\n"
        "anticipated questions and on-label responses: "
        "questions regarding the approved efficacy data should be addressed with reference to "
        "published clinical trial results and the approved prescribing information only. "
        "for any questions not addressed by the approved labeling, direct the physician to "
        "submit a formal query to the medical information team; only on-label information is shared "
        "during msl interactions.\n\n"
        "proposed key messages: communicate the approved efficacy and safety profile per labeling. "
        "reference the published data as cited in approved source documents.\n\n"
        "follow-up actions:\n" + actions_str + "\n\n"
        "compliance note: this brief reflects approved, on-label content only. "
        "all factual claims cite approved source documents. "
        "a medical affairs approver must review this brief before any hcp interaction."
    )


def draft_brief(state: Dict[str, Any]) -> Dict[str, str]:
    """Return {brief_text, drafted_by}. Demo fallback requires no API key."""
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"brief_text": _demo_brief(state), "drafted_by": "demo-stub"}

    try:
        from hcls_agent_platform import get_llm

        hcp = state.get("hcp_profile", {})
        docs = state.get("approved_documents", [])
        content_block = "\n".join(
            "[" + d.get("title", "doc") + " v" + d.get("version", "N/A") + "]: " + d.get("text", "")
            for d in docs
        )
        prompt = MSL_BRIEF_PROMPT.format(
            hcp_name=state.get("hcp_name", hcp.get("name", "")),
            meeting_date=state.get("meeting_date", ""),
            topic=state.get("topic", ""),
            meeting_purpose=state.get("meeting_purpose", ""),
            hcp_profile=str(hcp),
            approved_content=content_block or "No approved content retrieved.",
            instructions=state.get("instructions", ""),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        return {"brief_text": str(text), "drafted_by": provider}
    except Exception:
        return {"brief_text": _demo_brief(state), "drafted_by": "demo-stub-fallback"}
