"""
Check Lambda — deterministic quality gate.

Runs core.route() which internally calls:
  * core.phi_check()               — SSN / PHI leak detection
  * core.grounding_findings()      — ungrounded numbers in narrative
  * core.required_elements_check() — ICH E2B(R3) required narrative elements
  * ICSR validity gate             — escalate if case was never valid

Sets routing.action to APPROVE_DRAFT / REVISE / ESCALATE and bumps
revision_count when looping back to Draft.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared import audit, ok
import core


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    case_state = dict(body)
    audit_trail = case_state.pop("audit_trail", [])
    narrative = case_state.get("narrative_text", "")
    revision_count = int(case_state.get("revision_count", 0))

    routing = core.route(case_state, narrative, revision_count)
    case_state["routing"] = routing

    if routing["action"] == "REVISE":
        case_state["revision_count"] = revision_count + 1

    case_state["audit_trail"] = audit_trail
    trail_entry = audit(
        "check",
        {
            "case_id": case_state.get("case_id"),
            "action": routing["action"],
            "phi_findings": len(routing.get("phi_findings", [])),
            "grounding_issues": len(routing.get("grounding_findings", [])),
            "missing_elements": len(routing.get("missing_elements", [])),
            "revision_count": case_state["revision_count"],
        },
    )
    case_state["audit_trail"].append(trail_entry)

    return ok(case_state)
