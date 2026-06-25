"""Draft Lambda — exception report. Strands/Bedrock if available, else deterministic demo."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import audit, ok


def _demo_report(s: Dict[str, Any]) -> str:
    bid, prod = s.get("batch_id", "an unspecified batch"), s.get("product", "an unspecified product")
    exc = s.get("exceptions") or []
    if not exc:
        body = (f"Reviewed by exception, batch {bid} ({prod}) had no exceptions found. All in-process "
                f"parameters were within limits, all quality-control results were within specification, "
                f"and all required steps were recorded and e-signed. Recommendation: RELEASE.")
    else:
        lines = "; ".join(f"{e['code']} ({e['severity']}) at {e['step']}: {e['detail']}" for e in exc)
        body = (f"Reviewed by exception, batch {bid} ({prod}) had {len(exc)} exception(s) found "
                f"({s.get('critical_count', 0)} critical): {lines}. Recommendation: HOLD pending QA disposition.")
    return body + " This is a recommendation for QA sign-off; no batch disposition has been made."


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    state = dict(body)
    report, drafted_by = _demo_report(state), "demo-stub"
    if os.getenv("EXTRACT_MODE", "").lower() != "demo" and os.getenv("BEDROCK_REGION"):
        try:  # pragma: no cover - requires Bedrock
            from strands_agent import draft_with_strands
            report = draft_with_strands(state)
            drafted_by = "bedrock-strands"
        except Exception:
            report, drafted_by = _demo_report(state), "demo-stub-fallback"
    state["exception_report"] = report
    state["report_drafted_by"] = drafted_by
    state["disposition_recommendation"] = "HOLD" if state.get("has_open_exceptions") else "RELEASE"
    state.setdefault("audit_trail", []).append(
        audit("draft", {"batch_id": state.get("batch_id"), "drafted_by": drafted_by}))
    return ok(state)
