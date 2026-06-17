"""
Strands drafter — the LLM DRAFTING layer for the native Quality CAPA rebuild.

Drafts a CAPA plan from assembled, classified quality event evidence. It does NOT
decide severity, routing, or whether to create a CAPA in the QMS — that is core.py
(deterministic) and a Qualified Person (HITL via Step Functions waitForTaskToken).
Bedrock via Strands, with a demo fallback so the pipeline runs without an AWS account.
"""
from __future__ import annotations

import os
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a senior quality assurance specialist drafting CAPA plans for a regulated "
    "pharmaceutical manufacturer under GMP/GCP (21 CFR Part 820, ICH Q10). "
    "Draft corrective actions (what, who, by when), preventive actions (systemic changes), "
    "and effectiveness monitoring criteria. Use ONLY the provided evidence. "
    "Never speculate beyond the data. Never use absolute causal language. "
    "A Qualified Person must review and approve all CAPA plans before implementation."
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


def _demo_draft(evidence: Dict[str, Any]) -> str:
    complaint_id = evidence.get("complaint_id", "COMP-XXX")
    event_type = (evidence.get("event_type") or "complaint").lower()
    severity = (evidence.get("severity") or "major").lower()
    product = evidence.get("product", "the product")
    lot = evidence.get("lot_number", "the lot")
    desc = evidence.get("description", "quality event")
    n_similar = evidence.get("similar_event_count", 0)
    root_causes = evidence.get("root_cause_hypotheses", ["root cause under investigation"])

    rca_lines = "; ".join(str(rc) for rc in root_causes[:3])
    return (
        f"Corrective and preventive action plan for {event_type} {complaint_id} "
        f"(severity: {severity}, product: {product}, lot: {lot}).\n\n"
        f"Event description: {desc}\n\n"
        f"Trend review: {n_similar} similar event(s) identified in the quality management system.\n\n"
        f"Root cause hypotheses under investigation: {rca_lines}.\n\n"
        "Corrective actions: "
        "1. Immediate containment — quarantine affected lot(s) pending investigation. Due: immediately. "
        "2. Root cause investigation — complete five-why or fishbone analysis. "
        "Owner: quality assurance manager. Due: 15 business days. "
        "3. Targeted correction based on confirmed root cause. Owner: process owner. Due: 30 business days.\n\n"
        "Preventive actions: "
        "1. Update standard operating procedures to incorporate lessons learned. "
        "2. Retrain affected personnel. Owner: training manager. Due: 30 business days. "
        "3. Implement enhanced monitoring for similar processes.\n\n"
        "Effectiveness monitoring: track recurrence rate over 90 days; target: zero repeat events. "
        "Review metrics at 30, 60, and 90 days post-implementation.\n\n"
        "Regulatory assessment: qualified person to evaluate whether this event meets applicable "
        "reporting thresholds under current regulatory requirements.\n\n"
        "This draft requires qualified person review and approval before implementation."
    )


def draft_capa_plan(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Return {capa_plan, drafted_by}. Demo fallback requires no AWS account."""
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {"capa_plan": _demo_draft(evidence), "drafted_by": "demo-stub"}
    try:
        from strands import Agent

        agent = Agent(model=_bedrock_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
        result = agent(f"Draft a CAPA plan from this quality event evidence:\n{evidence}")
        text = getattr(result, "message", None) or str(result)
        return {"capa_plan": str(text), "drafted_by": "bedrock"}
    except Exception:
        return {"capa_plan": _demo_draft(evidence), "drafted_by": "demo-stub-fallback"}
