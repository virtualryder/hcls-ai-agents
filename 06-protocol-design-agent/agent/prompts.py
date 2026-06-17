# agent/prompts.py
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
    "You are a senior clinical scientist supporting protocol design for a sponsor. "
    "Draft protocol sections (endpoints, eligibility criteria, study schedule) that are "
    "grounded in regulatory guidance and real-world feasibility data. "
    "Use ONLY the guidance and data provided. Never invent precedent studies, patient counts, "
    "or regulatory requirements. Write in ICH E6 / GCP-compliant language. "
    "A qualified Medical/Clinical Reviewer must approve all protocol content before submission."
)

PROTOCOL_SECTIONS_PROMPT = register(
    "06-protocol-design", "protocol_sections", 1,
    """Draft protocol sections for a {phase} study in {indication}.
Therapeutic area: {therapeutic_area}
Primary objective: {primary_objective}
Target population: {target_population}
Study design: {study_design}

Regulatory guidance identified:
{guidance}

Feasibility cohort estimate (de-identified RWD):
{cohort_estimate}

Author instructions:
{instructions}

Draft the following sections:
1. ENDPOINTS: Primary and key secondary endpoints with measurement methods.
2. ELIGIBILITY CRITERIA: Key inclusion and exclusion criteria (GCP-compliant).
3. STUDY SCHEDULE: Visit schedule with key assessments at each timepoint.

Requirements:
- Ground all endpoint choices in the regulatory guidance above.
- Eligibility must be operationally feasible given the cohort estimate.
- Schedule should be consistent with GCP and patient burden considerations.
- 300-600 words total. ICH E6 language. No invented precedent.
"""
)
