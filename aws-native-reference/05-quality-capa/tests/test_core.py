"""Tests for the deterministic native core (no AWS, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core

EVIDENCE = {
    "complaint_id": "COMP-2026-001",
    "product": "Demo-Parenteral",
    "lot_number": "LOT-2026-001",
    "site": "SITE-MFG-01",
    "severity": "MAJOR",
    "risk_level": "MEDIUM",
    "similar_event_count": 2,
    "monitoring_days": 90,
    "correction_days": 30,
}


def test_clean_draft_routes_to_review():
    draft = (
        "Corrective actions: quarantine affected lot pending investigation. "
        "Preventive actions: update standard operating procedures; retrain personnel. "
        "Effectiveness monitoring: track recurrence rate over 90 days; target zero repeat events. "
        "Qualified person must review and approve this plan."
    )
    r = core.route(EVIDENCE, draft, 0)
    assert r["next"] == "HumanReviewGate"
    assert r["action"] == "APPROVE_CAPA"


def test_speculative_language_triggers_revision():
    draft = (
        "We will definitely prevent all future events — 100% sure this corrective action "
        "will work. Preventive actions: update sop. Effectiveness: monitor recurrence. "
        "Qualified person to review."
    )
    r = core.route(EVIDENCE, draft, 0)
    assert r["next"] == "Draft"
    assert r["action"] == "REVISE"


def test_missing_corrective_triggers_revision():
    draft = (
        "Preventive actions: update sop; retrain personnel. "
        "Effectiveness: monitor recurrence. Qualified person to review."
    )
    r = core.route(EVIDENCE, draft, 0)
    assert r["action"] == "REVISE"
    assert any("corrective_action" in c for c in r["compliance"])


def test_ungrounded_number_triggers_revision():
    draft = (
        "Corrective actions: quarantine lot. Preventive actions: retrain 99999 staff. "
        "Effectiveness: monitor recurrence. Qualified person to review."
    )
    r = core.route(EVIDENCE, draft, 0)
    assert r["next"] == "Draft" and r["action"] == "REVISE"
    assert any("99999" in g for g in r["grounding"])


def test_revision_count_exhausted_routes_to_review():
    draft = (
        "Preventive actions: update sop. Effectiveness: monitor recurrence. "
        "Qualified person to review."
    )
    r = core.route(EVIDENCE, draft, revision_count=1)
    assert r["next"] == "HumanReviewGate"


def test_classify_major_severity():
    result = core.classify_event("Visible particulate contamination in vial.", "MAJOR")
    assert result["severity"] == "MAJOR"
    assert result["risk_level"] == "MEDIUM"


def test_classify_critical_severity():
    result = core.classify_event("Patient harm reported. Death suspected.", "CRITICAL")
    assert result["severity"] == "CRITICAL"
    assert result["risk_level"] == "HIGH"


def test_classify_infers_from_description():
    result = core.classify_event("Temperature excursion in storage area detected.")
    assert result["severity"] == "MAJOR"


def test_grounding_flags_invented_number():
    findings = core.grounding_findings("We observed 99999 similar events.", EVIDENCE)
    assert any("99999" in f for f in findings)


def test_grounding_passes_state_numbers():
    # 2 is <= 12, so exempt. COMP-2026-001 is a string, not a number.
    findings = core.grounding_findings(
        "COMP-2026-001: 2 similar events found for LOT-2026-001.", EVIDENCE
    )
    assert findings == [], f"state-grounded text should pass: {findings}"
