# tools/disposition_drafter.py
# ============================================================
# Batch exception-report drafter — the LLM DRAFTING layer.
#
# Drafts a review-by-exception report from the scanned exceptions and batch facts.
# Uses the platform LLM factory (Anthropic default / Bedrock in-account) with a
# deterministic demo fallback so the pipeline runs with no API key. The report is
# grounded entirely in scanned exceptions; it never invents a deviation.
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import EXCEPTION_REPORT_PROMPT, SYSTEM_PROMPT


def _exception_lines(exceptions: List[Dict[str, Any]]) -> str:
    if not exceptions:
        return "  (none — batch reviewed with no exceptions found)"
    return "\n".join(
        f"  - [{e['severity']}] {e['code']} at {e['step']}: {e['detail']}"
        for e in exceptions
    )


def _demo_report(state: Dict[str, Any]) -> str:
    """Deterministic demo exception report — all values sourced from state."""
    batch_id = state.get("batch_id") or "an unspecified batch"
    product = state.get("product") or "an unspecified product"
    exceptions = state.get("exceptions") or []
    count = state.get("exception_count", len(exceptions))
    critical = state.get("critical_count", 0)

    if count == 0:
        body = (
            f"Reviewed by exception, batch {batch_id} ({product}) had no exceptions found. "
            f"All in-process parameters were within limits, all quality-control results were "
            f"within specification, and all required steps were recorded and e-signed. "
            f"Recommendation: RELEASE."
        )
    else:
        lines = "; ".join(
            f"{e['code']} ({e['severity']}) at {e['step']}: {e['detail']}" for e in exceptions
        )
        body = (
            f"Reviewed by exception, batch {batch_id} ({product}) had "
            f"{count} exception(s) found ({critical} critical): {lines}. "
            f"Recommendation: HOLD pending QA disposition."
        )
    return body + " This is a recommendation for QA sign-off; no batch disposition has been made."


def draft(state: Dict[str, Any]) -> Dict[str, str]:
    """Return {exception_report, report_drafted_by}. Demo fallback needs no API key."""
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"exception_report": _demo_report(state), "report_drafted_by": "demo-stub"}

    try:
        from hcls_agent_platform import get_llm

        prompt = EXCEPTION_REPORT_PROMPT.format(
            batch_id=state.get("batch_id") or "unknown",
            product=state.get("product") or "unknown",
            right_first_time=state.get("right_first_time", False),
            exception_count=state.get("exception_count", 0),
            critical_count=state.get("critical_count", 0),
            exception_lines=_exception_lines(state.get("exceptions") or []),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        return {"exception_report": str(text), "report_drafted_by": provider}
    except Exception:
        return {"exception_report": _demo_report(state), "report_drafted_by": "demo-stub-fallback"}
