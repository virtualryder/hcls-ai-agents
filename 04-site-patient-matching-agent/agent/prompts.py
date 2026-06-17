# agent/prompts.py
# ============================================================
# Prompts for the Site Patient Matching agent.
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
    "You are a clinical operations analyst specializing in trial site feasibility and "
    "patient recruitment. Your role is to translate eligibility criteria into computable "
    "cohort logic, rank sites by potential patient pool from de-identified RWD, and flag "
    "demographic under-representation to ensure equitable trial participation. "
    "PHI stays at source systems — you work only with aggregate, de-identified counts. "
    "Use ONLY the data provided. A human must approve the ranked list before any site outreach."
)

SITE_RANKING_PROMPT = register(
    "04-site-patient-matching", "site_ranking_report", 1,
    """Draft a site feasibility and patient matching report for study {study_id}.
Protocol: {protocol_id} | Indication: {indication}
Target enrollment: {target_enrollment}

Eligibility criteria:
{eligibility_criteria}

De-identified cohort results (aggregate only — no PHI):
{cohort_results}

Site statuses (CTMS):
{site_statuses}

Fairness flags (demographic under-representation):
{fairness_flags}

Requirements:
- Summarize the eligible patient pool size and geographic distribution.
- Rank the top sites by estimated eligible population.
- Flag any demographic groups under-represented vs. disease prevalence.
- Recommend site activation priorities.
- Note data limitations (RWD coverage gaps).
- 200-400 words. Factual, objective. PHI note: all data is aggregate/de-identified.
"""
)
