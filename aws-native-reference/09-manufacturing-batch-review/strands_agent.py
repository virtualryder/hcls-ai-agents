"""
Strands agent wrapper for the Manufacturing Batch-Review native rebuild.

The Strands/Bedrock layer drafts ONLY the human-readable exception report; the
deterministic core (scan / route) makes every pass/fail and routing decision.
Importing strands or boto3 is optional — draft_with_strands falls back to the
deterministic demo report if the runtime is unavailable.
"""
from __future__ import annotations

import os
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a manufacturing quality reviewer drafting a batch exception report for a QA reviewer. "
    "Use ONLY the scanned exceptions and batch facts provided; never invent deviations, limits, or "
    "results. Practice review by exception. State a recommendation (release or hold) but never assert "
    "a batch has been released or rejected — a QA reviewer authorizes that decision."
)


def _prompt(state: Dict[str, Any]) -> str:
    exc = state.get("exceptions") or []
    lines = "\n".join(f"  - [{e['severity']}] {e['code']} at {e['step']}: {e['detail']}" for e in exc) \
        or "  (none — no exceptions found)"
    return (f"Batch: {state.get('batch_id')}  Product: {state.get('product')}\n"
            f"Exceptions ({state.get('exception_count', 0)}, {state.get('critical_count', 0)} critical):\n"
            f"{lines}\n\nDraft an 80-200 word exception report with a RELEASE or HOLD recommendation, "
            f"closing with: 'This is a recommendation for QA sign-off; no batch disposition has been made.'")


def draft_with_strands(state: Dict[str, Any]) -> str:
    """Draft via Bedrock through Strands. Raises if the runtime is unavailable
    (caller falls back to the deterministic demo report)."""
    from strands import Agent  # type: ignore
    from strands.models import BedrockModel  # type: ignore

    model = BedrockModel(
        model_id=os.getenv("BEDROCK_NARRATIVE_MODEL_ID", "anthropic.claude-sonnet-4-6-20260601-v1:0"),
        region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
        guardrail_id=os.getenv("BEDROCK_GUARDRAIL_ID") or None,
    )
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT)
    return str(agent(_prompt(state)))
