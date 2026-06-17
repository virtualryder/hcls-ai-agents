"""
Strands drafter — the LLM DRAFTING layer for the native Protocol Design rebuild.

Drafts protocol sections (endpoints, eligibility, schedule) from assembled,
grounded evidence. It does NOT determine regulatory acceptability, routing, or
approve the protocol — that is core.py (deterministic) and a qualified Medical/
Clinical Reviewer (HITL via Step Functions waitForTaskToken). Bedrock via Strands,
with a demo fallback so the pipeline runs without an AWS account.
"""
from __future__ import annotations

import os
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a senior clinical scientist drafting protocol sections for a regulated clinical trial. "
    "Use ONLY the evidence, guidance, and feasibility data provided. "
    "Draft endpoints (primary and secondary), eligibility criteria (inclusion/exclusion), "
    "and a visit schedule. Never invent precedent studies, patient counts, or regulatory requirements. "
    "Write in ICH E6(R2) / GCP-compliant language. "
    "A qualified Medical/Clinical Reviewer must approve all content before submission."
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
    indication = evidence.get("indication", "the indication")
    phase = evidence.get("phase", "Phase 2")
    objective = evidence.get("primary_objective", "evaluate efficacy and safety")
    population = evidence.get("target_population", "adult patients")
    design = evidence.get("study_design", "randomized controlled trial")
    n_guidance = evidence.get("guidance_count", 0)
    total_eligible = evidence.get("total_eligible", "N/A")

    return (
        f"This {phase} protocol for {indication} is designed to {objective} "
        f"in {population} using a {design} design. "
        f"Regulatory guidance review identified {n_guidance} relevant document(s) to inform endpoint selection.\n\n"
        f"Endpoints: the primary endpoint is designed to {objective}, assessed at the primary "
        "analysis timepoint as specified in the applicable regulatory framework. "
        "Key secondary endpoints include patient-reported outcomes, safety events, and "
        "pharmacokinetic parameters where applicable.\n\n"
        f"Eligibility criteria: key inclusion criteria include {population.lower()} with confirmed "
        f"diagnosis of {indication}, adequate organ function per protocol-defined thresholds, and "
        "capacity to provide informed consent. Exclusion criteria include prior treatment with "
        "investigational agents within the prior cycle and active uncontrolled systemic disease. "
        f"Feasibility: de-identified real-world data estimates {total_eligible} potentially "
        "eligible patients in the intended site network (aggregate, de-identified).\n\n"
        "Study schedule: screening runs up to four weeks before first dose for baseline assessments. "
        f"The treatment phase follows the {design} assignment for the planned duration. "
        "Safety follow-up visits occur at 30 and 90 days after end of treatment. "
        "Final data collected at end of study.\n\n"
        "This draft requires review and approval by a qualified medical or clinical reviewer "
        "before finalization or submission to a health authority or ethics committee."
    )


def draft_protocol_sections(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Return {draft_protocol, drafted_by}. Demo fallback requires no AWS account."""
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {"draft_protocol": _demo_draft(evidence), "drafted_by": "demo-stub"}
    try:
        from strands import Agent

        agent = Agent(model=_bedrock_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
        result = agent(f"Draft protocol sections from this evidence:\n{evidence}")
        text = getattr(result, "message", None) or str(result)
        return {"draft_protocol": str(text), "drafted_by": "bedrock"}
    except Exception:
        return {"draft_protocol": _demo_draft(evidence), "drafted_by": "demo-stub-fallback"}
