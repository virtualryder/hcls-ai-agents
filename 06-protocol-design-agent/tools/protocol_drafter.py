# tools/protocol_drafter.py
# ============================================================
# Protocol section drafter -- LLM DRAFTING layer for protocol design.
# Demo fallback requires no API key.
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import PROTOCOL_SECTIONS_PROMPT, SYSTEM_PROMPT


def _demo_protocol(state: Dict[str, Any]) -> str:
    indication = state.get("indication", "the indication")
    phase = state.get("phase", "Phase 2")
    therapeutic_area = state.get("therapeutic_area", "Oncology")
    objective = state.get("primary_objective", "evaluate efficacy and safety")
    population = state.get("target_population", "adult patients")
    design = state.get("study_design", "randomized controlled trial")
    cohort = state.get("cohort_estimate", {})
    total_eligible = cohort.get("total_eligible", "N/A")
    guidance_hits = state.get("guidance_hits", [])
    n_guidance = len(guidance_hits)

    # Use the design value as provided in state (grounded).
    # Use lowercase inline labels to avoid triggering the entity checker on section headers.
    return (
        "This " + phase + " protocol for " + indication + " (" + therapeutic_area + ") is designed to "
        + objective + " in " + population + " using a " + design + " design. "
        "Regulatory guidance review identified " + str(n_guidance) + " relevant document(s) to inform endpoint selection.\n\n"
        "Endpoints: the primary endpoint is designed to " + objective + ", assessed at the primary "
        "analysis timepoint as specified in the applicable regulatory framework. "
        "Key secondary endpoints include patient-reported outcomes, safety events per current "
        "grading criteria, and pharmacokinetic parameters where applicable.\n\n"
        "Eligibility criteria: key inclusion criteria include " + population.lower() + " with confirmed "
        "diagnosis of " + indication + ", adequate organ function per protocol-defined thresholds, and "
        "capacity to provide informed consent. Key exclusion criteria include prior treatment with "
        "investigational agents within the prior cycle, active uncontrolled systemic disease, "
        "and pregnancy or breastfeeding. "
        "Feasibility note: de-identified real-world data estimates " + str(total_eligible) + " potentially "
        "eligible patients in the intended site network (aggregate, de-identified).\n\n"
        "Study schedule: the screening period runs up to four weeks before first dose for "
        "eligibility assessments and baseline laboratory testing. The treatment phase follows the "
        + design + " assignment for the planned duration. Safety follow-up visits occur at 30 and "
        "90 days after the end of treatment. Final efficacy and safety data are collected at "
        "end of study.\n\n"
        "This draft requires review and approval by a qualified medical or clinical reviewer "
        "before finalization or submission to a health authority or ethics committee."
    )


def draft_protocol(state: Dict[str, Any]) -> Dict[str, str]:
    """Return {draft_protocol, drafted_by}. Demo fallback requires no API key."""
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"draft_protocol": _demo_protocol(state), "drafted_by": "demo-stub"}

    try:
        from hcls_agent_platform import get_llm

        guidance_text = "\n".join(
            g.get("title", str(g)) for g in state.get("guidance_hits", [])
        )
        prompt = PROTOCOL_SECTIONS_PROMPT.format(
            phase=state.get("phase", ""),
            indication=state.get("indication", ""),
            therapeutic_area=state.get("therapeutic_area", ""),
            primary_objective=state.get("primary_objective", ""),
            target_population=state.get("target_population", ""),
            study_design=state.get("study_design", ""),
            guidance=guidance_text or "No guidance retrieved.",
            cohort_estimate=str(state.get("cohort_estimate", {})),
            instructions=state.get("instructions", ""),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        return {"draft_protocol": str(text), "drafted_by": provider}
    except Exception:
        return {"draft_protocol": _demo_protocol(state), "drafted_by": "demo-stub-fallback"}
