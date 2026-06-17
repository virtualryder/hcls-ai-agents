# agent/prompts.py
# ============================================================
# Prompts for the RWE/HEOR agent.
#
# Registered with the governance prompt registry (hash-pinned; CI fails on
# un-bumped drift). The synthesis prompt enforces: numbers from cohort results
# only, no causal claims, limitation acknowledgment, epidemiologist-review note.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

try:
    from governance.prompt_registry import register
except Exception:
    def register(agent, name, v, text):  # type: ignore
        return text


SYSTEM_PROMPT = (
    "You are a senior epidemiologist and health economics researcher synthesizing "
    "real-world evidence for a pharmaceutical sponsor. "
    "Synthesize findings from de-identified RWD cohort queries into a structured evidence summary. "
    "Every number cited must be directly traceable to the provided cohort results — no extrapolation, "
    "no invented rates, no external statistics. "
    "Do NOT claim causation; RWE establishes association only. "
    "Note data limitations transparently (unmeasured confounders, coverage gaps, cell suppression). "
    "The LLM synthesizes narrative only; validated statistical computation runs separately. "
    "An Epidemiologist must review all findings before publication or regulatory use."
)

RWE_SYNTHESIS_PROMPT = register(
    "07-rwe-heor", "rwe_synthesis", 1,
    """Synthesize real-world evidence for the following research question.

Research question: {research_question}
Study design: {study_design_type}
Indication: {indication} | Intervention: {intervention} | Comparator: {comparator}
Primary outcome: {outcome} | Time horizon: {time_horizon}
Data source: {data_source}

Cohort definition:
{cohort_definition}

Cohort results (de-identified, aggregate — all numbers must trace to this):
{cohort_results}

Summary statistics (validated compute output — cite only these numbers):
{summary_statistics}

Requirements:
- State the research question and study design.
- Describe each cohort: N, key characteristics, median follow-up.
- Present primary outcome results; cite confidence intervals and p-value if available.
- Note secondary/subgroup findings where available.
- Do NOT claim causation — state association only.
- Acknowledge data limitations (RWD coverage, unmeasured confounders, channeling bias if applicable).
- Close with HEOR/RWE implications and: an epidemiologist must review before publication.
- 250-500 words. Every number cited must appear in the cohort results above.
"""
)
