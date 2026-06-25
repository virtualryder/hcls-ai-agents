"""Unit tests for aws-native-reference/09-manufacturing-batch-review/core.py (no AWS, no model)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import core

CLEAN = {"batch_id": "B-1", "product": "P", "required_steps": ["S1"],
         "steps": [{"id": "S1", "name": "Dispensing", "value": 100.0, "lo": 99.0, "hi": 101.0,
                    "signed": True, "critical": True}]}


def test_scan_clean():
    r = core.scan(CLEAN, [{"test": "Assay", "result": 99.0, "lo": 95.0, "hi": 105.0, "status": "PASS"}])
    assert r["exception_count"] == 0 and r["critical_count"] == 0


def test_scan_oos_critical():
    r = core.scan(CLEAN, [{"test": "Assay", "result": 90.0, "lo": 95.0, "hi": 105.0, "status": "OOS"}])
    assert r["critical_count"] == 1 and r["exceptions"][0]["code"] == "OOS"


def test_scan_missing_and_unsigned_and_oolimit():
    rec = {"batch_id": "B-2", "required_steps": ["S1", "S9"],
           "steps": [{"id": "S1", "name": "Force", "value": 20.0, "lo": 10.0, "hi": 15.0,
                      "signed": False, "critical": False}]}
    codes = {e["code"] for e in core.scan(rec, [])["exceptions"]}
    assert {"OUT_OF_LIMIT", "UNSIGNED_STEP", "MISSING_STEP"} <= codes


def test_route_escalates_on_critical():
    state = {"batch_id": "B-3", "exception_count": 1, "critical_count": 1,
             "exceptions": [{"code": "OOS", "severity": "CRITICAL", "step": "Assay", "detail": "92 outside [95,105]"}]}
    report = ("Reviewed by exception, batch B-3 (P) had 1 exception(s) found (1 critical): "
              "OOS (CRITICAL) at Assay: 92 outside [95,105]. Recommendation: HOLD pending QA disposition. "
              "This is a recommendation for QA sign-off; no batch disposition has been made.")
    out = core.route(state, report, 0)
    assert out["action"] == "ESCALATE" and out["next"] == "QAReviewGate"


def test_route_recommends_release_when_clean():
    report = ("Reviewed by exception, batch B-1 (P) had no exceptions found. Recommendation: RELEASE. "
              "This is a recommendation for QA sign-off; no batch disposition has been made.")
    out = core.route({"batch_id": "B-1", "exception_count": 0, "critical_count": 0}, report, 0)
    assert out["action"] == "RECOMMEND_RELEASE" and out["next"] == "QAReviewGate"


def test_route_revises_on_ungrounded():
    # report references a number (777) not in corpus -> ungrounded -> REVISE
    report = "batch B-9 reviewed; lot 777 recommendation release QA sign-off no batch disposition"
    out = core.route({"batch_id": "B-9", "exception_count": 0, "critical_count": 0}, report, 0)
    assert out["action"] == "REVISE" and out["next"] == "Draft"


def test_required_elements_complete():
    report = ("Reviewed by exception, batch B-1 had no exceptions. Recommendation: RELEASE. "
              "This is a recommendation for QA sign-off; no batch disposition has been made.")
    assert core.required_elements(report) == []
