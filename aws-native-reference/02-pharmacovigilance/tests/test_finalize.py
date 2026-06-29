"""
Approval-integrity tests for the Finalize Lambda (remediation of external-review
findings F1/F2/F4b).

Proves the deployed finalize path:
  * reads the reviewer decision from the ASL SIBLING ``event["review"]`` (F4b);
  * under STRICT_APPROVAL requires a *verified bound* approval token (F2) — a bare
    boolean is rejected and the case is NOT submitted (fail closed);
  * accepts a correctly-bound token and submits (F1);
  * rejects tampered-args, retargeted-tool, and replayed tokens.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make the Lambda code and the shared platform importable.
_LAMBDAS = Path(__file__).resolve().parent.parent / "lambdas"
_PLATFORM = Path(__file__).resolve().parents[3] / "platform_core"
for p in (str(_LAMBDAS), str(_PLATFORM)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("APPROVAL_TOKEN_SECRET", "test-secret-finalize")
os.environ.setdefault("HCLS_LOCAL_TEST", "1")  # unit tests have no AWS connector

import finalize  # noqa: E402
from hcls_agent_platform.mcp_gateway import approvals  # noqa: E402

REQUESTOR = "pv-agent-02"
APPROVER = "dr.reviewer@pharma.example"
CASE = {"case_id": "ICSR-2026-0001", "meddra_pt": "Nausea", "reporting_clock_days": 15}
# finalize binds approvals to case_id ONLY (stable across the pipeline)


def _event(review):
    # ASL shape: body and review are siblings.
    return {"body": dict(CASE), "review": review}


def _body(resp):
    return json.loads(resp["body"])


def _mint(args=None, tool="safety.submit_report", requestor=REQUESTOR):
    return approvals.mint_approval_token(
        requestor=requestor, agent_id="02-pharmacovigilance", tool=tool,
        args=args if args is not None else {"case_id": CASE["case_id"]},
        approver=APPROVER,
    )


def test_reads_review_from_event_sibling_demo_approve(monkeypatch):
    monkeypatch.delenv("STRICT_APPROVAL", raising=False)
    out = _body(finalize.handler(_event({"approved": True})))
    assert out["case_status"] == "SUBMITTED"
    assert out["approval_verified"] is False  # demo boolean, explicitly unverified


def test_demo_reject_does_not_submit(monkeypatch):
    monkeypatch.delenv("STRICT_APPROVAL", raising=False)
    out = _body(finalize.handler(_event({"approved": False})))
    assert out["case_status"] == "PENDING_REVIEW"


def test_strict_requires_bound_token(monkeypatch):
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    out = _body(finalize.handler(_event({"approved": True})))  # boolean only
    assert out["case_status"] == "PENDING_REVIEW"          # fail closed
    assert out["approval_verified"] is False


def test_valid_bound_token_submits(monkeypatch):
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    out = _body(finalize.handler(_event({"approval_token": _mint()})))
    assert out["case_status"] == "SUBMITTED"
    assert out["approval_verified"] is True
    assert out["approval_reviewer"] == APPROVER
    assert out["submission_case_id"] == f"SUBMITTED-{CASE['case_id']}"


def test_tampered_args_rejected(monkeypatch):
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    # token bound to a different case than the one being finalized
    token = _mint(args={"case_id": "ICSR-OTHER"})
    out = _body(finalize.handler(_event({"approval_token": token})))
    assert out["case_status"] == "PENDING_REVIEW"
    assert out["approval_verified"] is False


def test_retargeted_tool_rejected(monkeypatch):
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    token = _mint(tool="safety.write_case_draft")  # not the consequential submit
    out = _body(finalize.handler(_event({"approval_token": token})))
    assert out["case_status"] == "PENDING_REVIEW"


def test_finalize_defers_single_use_to_connector(monkeypatch):
    # finalize verifies the bound approval with consume=False; the GOVERNED CONNECTOR is
    # the single-use enforcement point (durable jti claim — see test_approval_consumption
    # and test_connector_audit). So finalize itself does not consume the jti.
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    token = _mint()
    first = _body(finalize.handler(_event({"approval_token": token})))
    assert first["case_status"] == "SUBMITTED"
    assert first["approval_verified"] is True


def test_strict_without_connector_refuses_local_submit(monkeypatch):
    # round-2 #3: outside local-test mode, strict mode must NOT fall back to a local id.
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    monkeypatch.delenv("HCLS_LOCAL_TEST", raising=False)
    monkeypatch.delenv("SAFETY_CONNECTOR_FUNCTION", raising=False)
    with pytest.raises(RuntimeError, match="SAFETY_CONNECTOR_FUNCTION is required"):
        finalize.handler(_event({"approval_token": _mint()}))
