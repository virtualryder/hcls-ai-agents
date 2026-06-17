"""Tests for the deterministic native core (no AWS, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core


EVIDENCE = {"n_subjects": 450, "hba1c_reduction_pct": 1.2, "product": "Demo-Drug"}


def test_clean_draft_routes_to_review():
    draft = ("Purpose: support the application. In the study, 450 subjects showed an HbA1c "
             "reduction of 1.2 vs placebo. Benefit is favorable relative to risk. In conclusion, "
             "the data support a positive balance.")
    r = core.route(EVIDENCE, draft, 0)
    assert r["next"] == "HumanReviewGate" and r["action"] == "APPROVE_DRAFT"


def test_prohibited_language_escalates():
    draft = "Purpose: data show benefit. This is a miracle cure, completely safe. In conclusion, support."
    r = core.route(EVIDENCE, draft, 0)
    assert r["action"] == "ESCALATE"


def test_ungrounded_number_triggers_revision():
    draft = "Purpose: data study. 999 subjects had benefit and risk. In conclusion we support it."
    r = core.route(EVIDENCE, draft, 0)
    assert r["next"] == "Draft" and r["action"] == "REVISE"
    assert any("999" in g for g in r["grounding"])
