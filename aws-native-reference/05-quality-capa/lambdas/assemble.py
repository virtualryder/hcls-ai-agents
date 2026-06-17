"""
Assemble: classify the quality event, fetch similar events, and build the
grounding evidence corpus for the CAPA drafter.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from _shared import audit, ok


def handler(event: Dict[str, Any], _ctx: Any = None) -> Dict[str, Any]:
    state = dict(event)

    # Classify severity and risk from description
    classification = core.classify_event(
        state.get("description", ""),
        state.get("severity", ""),
    )
    state["classification"] = classification
    state["severity"] = classification["severity"]

    # Build grounding evidence corpus
    evidence = {
        "complaint_id": state.get("complaint_id"),
        "product": state.get("product"),
        "lot_number": state.get("lot_number"),
        "site": state.get("site"),
        "event_type": state.get("event_type"),
        "severity": classification["severity"],
        "risk_level": classification["risk_level"],
        "description": state.get("description"),
        "similar_event_count": len(state.get("similar_events", [])),
        "root_cause_hypotheses": state.get("root_cause_hypotheses", []),
    }
    state["evidence"] = evidence
    state.setdefault("revision_count", 0)

    return ok(audit(state, "Assembled quality event evidence corpus", "assemble"))
