# agent/prompts.py
# ============================================================
# Prompts for the Manufacturing Batch-Review agent.
#
# Registered with the governance prompt registry (hash-pinned; CI fails on
# un-bumped drift). The exception report must be grounded entirely in the scanned
# exceptions and batch facts — never invent a deviation, a limit, or a result.
# The disposition is a RECOMMENDATION; QA decides release/reject.
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
    "You are a manufacturing quality reviewer drafting a batch exception report for review "
    "by a qualified QA reviewer. Use ONLY the scanned exceptions and batch facts provided; "
    "never invent deviations, specification limits, results, or step names. Practice review "
    "by exception: summarize only what deviated and why it matters, in concise, factual, "
    "non-interpretive language. State a recommendation (release or hold) but never assert that "
    "a batch has been released or rejected — a qualified QA reviewer authorizes that decision."
)

EXCEPTION_REPORT_PROMPT = register(
    "09-manufacturing-batch-review", "exception_report", 1,
    """Draft a batch exception report for a QA reviewer from the following data.

Batch: {batch_id}  Product: {product}
Right-first-time: {right_first_time}
Exception count: {exception_count} (critical: {critical_count})
Exceptions:
{exception_lines}

Requirements:
- 80-200 words. Factual, grounded entirely in the exceptions and batch facts above.
- If there are zero exceptions, state the batch was reviewed with no exceptions found.
- For each exception, state the step, the severity, and the specific finding.
- Give a recommendation: "Recommendation: RELEASE" (no open exceptions) or
  "Recommendation: HOLD pending QA disposition" (one or more open exceptions).
- Do not invent additional deviations or results.
- Close with: "This is a recommendation for QA sign-off; no batch disposition has been made."
"""
)
