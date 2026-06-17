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
    "You are a senior quality assurance specialist drafting CAPA plans for a regulated "
    "pharmaceutical/device manufacturer under GMP/GCP (21 CFR Part 820, ICH Q10). "
    "Classify events accurately, identify root causes based ONLY on the provided data, "
    "and draft actionable, measurable CAPA steps with realistic timelines. "
    "Never speculate beyond the evidence; never minimize serious events. "
    "A Qualified Person must review and approve all CAPA plans before implementation."
)

CAPA_PLAN_PROMPT = register(
    "05-quality-capa", "capa_plan", 1,
    """Draft a CAPA plan for the following quality event.

Event ID: {complaint_id}
Type: {event_type} | Severity: {severity}
Product: {product} | Lot: {lot_number} | Site: {site}
Description: {description}

Similar historical events (for trend analysis):
{similar_events}

Root cause hypotheses:
{root_causes}

Requirements:
- State the event classification and risk level.
- List root cause hypotheses with supporting evidence from similar events.
- Draft corrective actions: what, who, by when, how verified.
- Draft preventive actions: systemic changes to prevent recurrence.
- Specify effectiveness checks (metrics, timeframe).
- Note if regulatory reporting is required.
- 250-500 words. GMP-compliant language. A Qualified Person reviews before any action is taken.
"""
)
