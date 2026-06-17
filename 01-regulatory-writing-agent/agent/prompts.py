# agent/prompts.py
# ============================================================
# Prompts for the Regulatory Writing agent.
#
# Prompts are part of the model under a GxP / model-risk posture, so they are
# registered with the governance prompt registry (hash-pinned; CI fails on
# un-bumped drift). Keep prompts factual, grounded, and free of promotional or
# off-label language by construction.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path

# Allow `from governance.prompt_registry import register` from the agent folder.
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

try:
    from governance.prompt_registry import register
except Exception:  # registry optional in standalone demo
    def register(agent, name, v, text):  # type: ignore
        return text


SYSTEM_PROMPT = (
    "You are a senior regulatory medical writer drafting content for a health-authority "
    "submission, for review by a qualified Regulatory Approver. Follow ICH/CTD conventions. "
    "Use ONLY the facts provided in the evidence; never invent figures, study results, "
    "endpoints, or institution names. Write in neutral, scientific, non-promotional language: "
    "do not use words like 'cure', 'guarantee', 'miracle', 'completely safe', or 'best-in-class', "
    "and do not make claims beyond the approved indication. Never state that a submission has "
    "been filed or accepted — a human authorizes that."
)

BENEFIT_RISK_SECTION_PROMPT = register(
    "01-regulatory-writing", "benefit_risk_section", 1,
    """Draft a {document_type} for {product} ({indication}) targeting {target_authority}.
Section reference: {section_ref}.

Author instructions:
{instructions}

Regulatory guidance in scope:
{guidance}

Source evidence (the ONLY facts you may use):
{evidence}

Requirements:
- Open with the purpose/objective of the section.
- Summarize the relevant data and results, citing the source reference.
- Present a balanced benefit-risk discussion (efficacy AND safety).
- Close with a clear, qualified conclusion.
- 150-400 words. Neutral, non-promotional, fully grounded in the evidence above.
"""
)
