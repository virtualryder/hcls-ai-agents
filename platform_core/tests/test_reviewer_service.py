"""Round-2 #2: the reviewer service authorizes the role, enforces separation of duties,
and mints a server-side bound token that finalize will accept."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT / "platform_core"),):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load():
    spec = importlib.util.spec_from_file_location(
        "reviewer_app", _ROOT / "services" / "reviewer-service" / "app.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


app = _load()
from hcls_agent_platform.mcp_gateway import approvals

BINDING = {"requestor": "pv-proc-1", "agent_id": "02-pharmacovigilance",
           "tool": "safety.submit_report", "args": {"case_id": "ICSR-1"}}
PENDING = {"task_token": "tok-123", "approval_binding": BINDING}
REVIEWER = {"sub": "pv-physician-9", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}


def test_approve_mints_verifiable_bound_token():
    out = app.build_review_decision(REVIEWER, PENDING, "approved")
    assert out["approved"] and out["task_token"] == "tok-123"
    tok = out["output"]["approval_token"]
    # the token verifies against the same binding finalize will use
    payload = approvals.verify_approval_token(
        tok, requestor=BINDING["requestor"], agent_id=BINDING["agent_id"],
        tool=BINDING["tool"], args=BINDING["args"])
    assert payload["approver"] == REVIEWER["sub"]


def test_unauthorized_role_rejected():
    with pytest.raises(app.ReviewUnauthorized, match="not entitled"):
        app.build_review_decision({"sub": "x", "custom:hcls_role": "PV_PROCESSOR"}, PENDING, "approved")


def test_missing_subject_rejected():
    with pytest.raises(app.ReviewUnauthorized, match="no authenticated"):
        app.build_review_decision({"custom:hcls_role": "PV_MEDICAL_REVIEWER"}, PENDING, "approved")


def test_self_approval_rejected():
    claims = {"sub": "pv-proc-1", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}  # == requestor
    with pytest.raises(app.ReviewUnauthorized, match="separation of duties"):
        app.build_review_decision(claims, PENDING, "approved")


def test_reject_sends_no_token():
    out = app.build_review_decision(REVIEWER, PENDING, "rejected")
    assert out["approved"] is False and "approval_token" not in out["output"]
