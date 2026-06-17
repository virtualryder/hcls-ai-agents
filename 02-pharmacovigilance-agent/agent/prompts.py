# agent/prompts.py
# ============================================================
# Prompts for the Pharmacovigilance ICSR intake agent.
#
# Prompts are registered with the governance prompt registry (hash-pinned;
# CI fails on un-bumped drift). Keep prompts factual, grounded in case state,
# and free of fabricated medical details by construction. The narrative must
# satisfy ICH E2B(R3) narrative elements and GVP Module VI requirements.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

try:
    from governance.prompt_registry import register
except Exception:  # registry optional in standalone demo
    def register(agent, name, v, text):  # type: ignore
        return text


SYSTEM_PROMPT = (
    "You are a pharmacovigilance medical writer drafting an ICSR narrative for review "
    "by a qualified PV Medical Reviewer. Use ONLY the case facts provided; never invent "
    "patient identifiers, dose values, event descriptions, or outcomes. Follow ICH E2B(R3) "
    "narrative conventions: who (patient demographics, reporter), what product (drug/dose/route), "
    "what event, when (onset/duration), seriousness and causality assessment. Write in concise, "
    "factual, non-interpretive clinical language. Never state that a case has been submitted "
    "to a regulatory authority — a qualified PV Medical Reviewer authorizes that action."
)

ICSR_NARRATIVE_PROMPT = register(
    "02-pharmacovigilance", "icsr_narrative", 1,
    """Draft an ICSR narrative for a PV Medical Reviewer based on the following case data.

Patient: {patient_age}, {patient_sex}
Reporter: {reporter_name} ({reporter_type}), {reporter_country}
Suspect product: {suspect_drug}, dose {suspect_dose}, route {suspect_route}
Indication: {suspect_indication}
Adverse event: {event_description}
Onset: {event_onset_date} (time to onset: {time_to_onset_days} days)
Outcome: {event_outcome}
Dechallenge: {dechallenge} | Rechallenge: {rechallenge}
MedDRA PT: {meddra_pt} ({meddra_pt_code}) — SOC: {meddra_soc}
WHODrug: {whodrug_name} (ATC: {whodrug_atc})
Seriousness: {seriousness_criteria}
Expectedness: {expectedness}
Causality: {causality_assessment}

Requirements:
- 100-250 words. Factual, grounded entirely in the data above.
- Cover: who (patient and reporter), what product (drug, dose, route), what event,
  when (onset/days), seriousness, causality, and outcome.
- Do not invent additional clinical details.
- Close with: "This case is being processed for PV Medical Reviewer sign-off; no
  submission has been made."
"""
)
