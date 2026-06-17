"""
Strands drafter — the LLM DRAFTING layer for the native rebuild.

Drafts a regulated section from assembled, grounded evidence. It does NOT decide
compliance, routing, or whether to submit — that is core.py (deterministic) and a
Regulatory Approver (HITL via Step Functions waitForTaskToken). Bedrock via
Strands, with a demo fallback so the pipeline runs without an AWS account.
"""
from __future__ import annotations

import os
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a senior regulatory medical writer drafting submission content for human "
    "review. Use only the facts provided. Cover purpose, data, a balanced benefit-risk "
    "discussion, and a qualified conclusion. Never use promotional or absolute language "
    "(cure, guarantee, completely safe) and never claim a submission has been filed."
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
    product = evidence.get("product", "the product")
    indication = evidence.get("indication", "the indication")
    n = evidence.get("n_subjects", "the enrolled")
    endpoint = evidence.get("primary_endpoint", "the primary endpoint")
    effect = evidence.get("hba1c_reduction_pct") or evidence.get("effect_size") or "the observed effect"
    src = evidence.get("source_ref", "the source record")
    return (
        f"Purpose: this section supports the application for {product} in {indication}. In the "
        f"pivotal study, {n} subjects were evaluated; {endpoint} demonstrated a result of {effect} "
        f"relative to comparator. The safety profile was consistent with the class, with no new "
        f"signals identified. The benefit is favorable relative to the identified risks. Source: "
        f"{src}. In conclusion, the data support a positive benefit-risk balance for the proposed "
        f"indication. Prepared for Regulatory Approver review; no submission has been made."
    )


def draft_section(evidence: Dict[str, Any]) -> Dict[str, Any]:
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {"draft": _demo_draft(evidence), "drafted_by": "demo-stub"}
    try:
        from strands import Agent

        agent = Agent(model=_bedrock_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
        result = agent(f"Draft the regulated section from this evidence:\n{evidence}")
        text = getattr(result, "message", None) or str(result)
        return {"draft": str(text), "drafted_by": "bedrock"}
    except Exception:
        return {"draft": _demo_draft(evidence), "drafted_by": "demo-stub-fallback"}
