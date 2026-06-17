"""
Strands drafter — the LLM DRAFTING layer for the RWE/HEOR native rebuild.

Synthesizes narrative from validated cohort statistics. It does NOT generate
statistical estimates — those come from the validated compute layer (Assemble).
Bedrock via Strands, with a demo fallback so the pipeline runs without AWS.
"""
from __future__ import annotations

import os
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a senior epidemiologist synthesizing real-world evidence for a pharmaceutical sponsor. "
    "Synthesize findings from de-identified RWD cohort queries into a structured evidence summary. "
    "Every number cited must be directly traceable to the provided cohort results — no extrapolation, "
    "no invented rates, no external statistics. "
    "Do NOT claim causation; RWE establishes association only. "
    "Acknowledge data limitations transparently. "
    "An Epidemiologist must review all findings before publication or regulatory use."
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


def _demo_synthesis(cohort_results: Dict[str, Any], evidence: Dict[str, Any]) -> str:
    indication = evidence.get("indication", "the indication")
    intervention = evidence.get("intervention", "intervention")
    comparator = evidence.get("comparator", "comparator")
    outcome = evidence.get("outcome", "primary outcome")
    time_horizon = evidence.get("time_horizon", "the study period")
    data_source = evidence.get("data_source", "real-world data source")
    n_int = cohort_results.get("n_intervention", "N/A")
    n_comp = cohort_results.get("n_comparator", "N/A")
    rate_int = cohort_results.get("outcome_rate_intervention", "N/A")
    rate_comp = cohort_results.get("outcome_rate_comparator", "N/A")
    follow_up = cohort_results.get("median_follow_up_months", "N/A")
    p_val = cohort_results.get("p_value", "not reported")
    completeness = cohort_results.get("data_completeness_pct", "N/A")

    return (
        "this retrospective cohort study using " + data_source + " compared "
        + intervention + " versus " + comparator + " in patients with " + indication
        + ", with " + outcome + " assessed over " + time_horizon + ". "
        "the " + intervention + " cohort included " + str(n_int) + " patients; "
        "the " + comparator + " cohort included " + str(n_comp) + " patients. "
        "median follow-up was " + str(follow_up) + " months. "
        "the observed " + outcome + " rate was " + str(rate_int) + " in the "
        + intervention + " group versus " + str(rate_comp) + " in the "
        + comparator + " group (p=" + str(p_val) + "). "
        "statistical analyses were conducted by a validated compute pipeline; "
        "the llm synthesizes narrative only and does not generate statistical estimates. "
        "data completeness: " + str(completeness) + "%. "
        "limitations: unmeasured confounders may be present in this observational analysis. "
        "these findings establish association and do not demonstrate causality. "
        "an epidemiologist must review before publication or regulatory use."
    )


def draft_synthesis(
    cohort_results: Dict[str, Any], evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """Return {synthesis, drafted_by}."""
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {
            "synthesis": _demo_synthesis(cohort_results, evidence),
            "drafted_by": "demo-stub",
        }
    try:
        from strands import Agent

        agent = Agent(model=_bedrock_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
        prompt = (
            "Synthesize real-world evidence from these cohort results:\n"
            f"Evidence context: {evidence}\n"
            f"Cohort results (de-identified, aggregate): {cohort_results}\n"
            "Requirements: numbers only from cohort results, no causation claims, "
            "acknowledge limitations, epidemiologist review required."
        )
        result = agent(prompt)
        text = getattr(result, "message", None) or str(result)
        return {"synthesis": str(text), "drafted_by": "bedrock"}
    except Exception:
        return {
            "synthesis": _demo_synthesis(cohort_results, evidence),
            "drafted_by": "demo-stub-fallback",
        }
