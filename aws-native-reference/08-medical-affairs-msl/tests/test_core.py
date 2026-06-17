"""Tests for the deterministic MSL native core (no AWS, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core

_APPROVED_DOCS = [
    {
        "doc_id": "DOC-PI-001",
        "title": "Demo-Drug Prescribing Information",
        "version": "3.0",
        "status": "APPROVED",
        "text": (
            "Demo-Drug is indicated for type 2 diabetes mellitus in adults. "
            "In STUDY-301 (n=450), Demo-Drug reduced HbA1c by 1.2 percentage points vs placebo. "
            "Common adverse events: upper respiratory infection (8%), nausea (6%). "
            "Contraindicated in severe renal impairment (eGFR < 30)."
        ),
    },
]


def test_clean_brief_routes_to_review():
    brief = (
        "pre-call brief for meeting with Dr. Jane Smith. "
        "hcp background: endocrinology specialist with interests in type 2 diabetes. "
        "approved data per Demo-Drug Prescribing Information: indicated for type 2 diabetes. "
        "compliance note: on-label content only; medical affairs approver review required. "
        "follow-up: log interaction in crm system."
    )
    r = core.route(brief, _APPROVED_DOCS, 0)
    assert r["next"] == "HumanReviewGate"
    assert r["action"] == "APPROVE_BRIEF"


def test_off_label_escalates():
    brief = (
        "this brief discusses off-label use of Demo-Drug for pediatric patients. "
        "hcp background noted. approved data cited. compliance review required."
    )
    r = core.route(brief, _APPROVED_DOCS, 0)
    assert r["action"] == "ESCALATE"
    assert any("off-label" in c for c in r["compliance"])


def test_promotional_escalates():
    brief = (
        "Demo-Drug is best-in-class for all diabetic patients. "
        "hcp background: endocrinology. approved labeling cited. compliance review required."
    )
    r = core.route(brief, _APPROVED_DOCS, 0)
    assert r["action"] == "ESCALATE"
    assert any("promotional" in c for c in r["compliance"])


def test_ungrounded_number_triggers_revision():
    brief = (
        "we found 99999 patients responded. hcp background noted. "
        "approved labeling for type 2 diabetes. compliance review required. "
        "follow-up: log in crm."
    )
    r = core.route(brief, _APPROVED_DOCS, 0)
    assert r["next"] == "Draft"
    assert r["action"] == "REVISE"
    assert any("99999" in g for g in r["grounding"])


def test_grounded_numbers_pass():
    # 450 is in the approved doc text, 1.2 <= 12 exempt, 8 <= 12 exempt
    brief = (
        "in study-301 (n=450), the drug reduced hba1c by 1.2 percentage points. "
        "hcp background: endocrinology. approved prescribing information cited. "
        "compliance note: on-label only; medical affairs approver review required. "
        "follow-up: log in crm."
    )
    r = core.route(brief, _APPROVED_DOCS, 0)
    assert r["action"] in ("APPROVE_BRIEF", "REVISE")  # no grounding failure on 450
    assert not any("450" in g for g in r["grounding"]), "450 is in corpus and should not be flagged"


def test_revision_count_prevents_infinite_loop():
    brief = (
        "99999 patients noted. hcp background: specialist. "
        "approved labeling cited. compliance review required. follow-up in crm."
    )
    r = core.route(brief, _APPROVED_DOCS, revision_count=1)
    assert r["next"] == "HumanReviewGate"
