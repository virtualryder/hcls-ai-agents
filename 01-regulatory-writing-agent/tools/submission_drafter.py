# tools/submission_drafter.py
# ============================================================
# Submission drafter — the LLM DRAFTING layer.
#
# Drafts a regulated section from assembled, grounded evidence. The model only
# writes prose a human reviews; it does not decide strategy or finalize anything.
# Uses the platform LLM factory (Anthropic default / Bedrock in-account) with a
# deterministic demo fallback so the pipeline runs with no API key.
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import BENEFIT_RISK_SECTION_PROMPT, SYSTEM_PROMPT


def _evidence_block(state: Dict[str, Any]) -> str:
    sd = state.get("study_data", {})
    facts = [f"{k}: {v}" for k, v in sd.items()]
    docs = [f"{d.get('title', 'doc')} (v{d.get('version', '?')}): {d.get('text', '')}"
            for d in state.get("source_documents", [])]
    return "Structured facts:\n" + "\n".join(facts) + "\n\nSource documents:\n" + "\n".join(docs)


def _demo_draft(state: Dict[str, Any]) -> str:
    sd = state.get("study_data", {})
    product = state.get("product", "the product")
    indication = state.get("indication", "the indication")
    n = sd.get("n_subjects", "the enrolled")
    endpoint = sd.get("primary_endpoint", "the primary endpoint")
    effect = sd.get("hba1c_reduction_pct") or sd.get("effect_size") or "the observed effect"
    comparator = sd.get("comparator", "comparator")
    src = sd.get("source_ref", state.get("section_ref", "the source record"))
    return (
        f"Purpose: this {state.get('document_type', 'section').lower().replace('_', ' ')} "
        f"supports the application for {product} in {indication}. "
        f"In the pivotal study, {n} subjects were evaluated; {endpoint} demonstrated a result of "
        f"{effect} relative to {comparator}. The observed safety profile was consistent with the "
        f"established class, and no new safety signals were identified during the analysis. The "
        f"benefit is considered favorable relative to the identified risks. Source: {src}. "
        f"In conclusion, the available data support a positive benefit-risk balance for the "
        f"proposed indication, subject to routine pharmacovigilance. This draft is prepared for "
        f"Regulatory Approver review; no submission has been made."
    )


def draft_section(state: Dict[str, Any]) -> Dict[str, str]:
    """Return {draft_text, drafted_by}. Demo fallback requires no API key."""
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"draft_text": _demo_draft(state), "drafted_by": "demo-stub"}

    try:
        from hcls_agent_platform import get_llm

        prompt = BENEFIT_RISK_SECTION_PROMPT.format(
            document_type=state.get("document_type", "section"),
            product=state.get("product", ""),
            indication=state.get("indication", ""),
            target_authority=state.get("target_authority", ""),
            section_ref=state.get("section_ref", ""),
            instructions=state.get("instructions", ""),
            guidance="\n".join(g.get("title", "") for g in state.get("guidance_hits", [])),
            evidence=_evidence_block(state),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        return {"draft_text": str(text), "drafted_by": provider}
    except Exception:
        return {"draft_text": _demo_draft(state), "drafted_by": "demo-stub-fallback"}
