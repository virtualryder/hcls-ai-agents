"""
Round-2 #1: approval replay protection must be DURABLE, not process-local.

When APPROVAL_CONSUMPTION_TABLE is set, verify() must claim each jti through the
atomic conditional-create path so a token replayed in a *different* execution
environment is rejected. We simulate the shared DynamoDB table with an in-memory
dict injected over the two small indirections, which is exactly what a second
Lambda environment would share.
"""
from __future__ import annotations

import os
import pytest

from hcls_agent_platform.mcp_gateway import approvals

REQ, APP = "pv-agent-02", "reviewer-1"
KW = dict(agent_id="02-pharmacovigilance", tool="safety.submit_report",
          args={"case_id": "ICSR-1"})


def _mint():
    return approvals.mint_approval_token(requestor=REQ, approver=APP, **KW)


@pytest.fixture
def shared_table(monkeypatch):
    """A single dict standing in for the shared DynamoDB consumption table."""
    store: set[str] = set()

    def claim(table, jti):
        if jti in store:
            return False
        store.add(jti)
        return True

    def exists(table, jti):
        return jti in store

    monkeypatch.setenv("APPROVAL_CONSUMPTION_TABLE", "hcls-approval-consumption")
    monkeypatch.setattr(approvals, "_ddb_claim", claim)
    monkeypatch.setattr(approvals, "_ddb_exists", exists)
    return store


def test_durable_first_use_succeeds_then_replay_rejected(shared_table):
    tok = _mint()
    approvals.verify_approval_token(tok, requestor=REQ, **KW)  # first use claims jti
    with pytest.raises(approvals.ApprovalInvalid, match="replay"):
        approvals.verify_approval_token(tok, requestor=REQ, **KW)  # durable replay denied


def test_replay_denied_across_simulated_environments(shared_table):
    # Two different processes sharing the same table: clear the in-memory fallback
    # between calls to prove rejection comes from the DURABLE store, not _USED_JTIS.
    tok = _mint()
    approvals.verify_approval_token(tok, requestor=REQ, **KW)
    approvals._USED_JTIS.clear()  # simulate a cold start / different env
    with pytest.raises(approvals.ApprovalInvalid, match="replay"):
        approvals.verify_approval_token(tok, requestor=REQ, **KW)


def test_consume_false_does_not_claim(shared_table):
    tok = _mint()
    approvals.verify_approval_token(tok, requestor=REQ, consume=False, **KW)
    # not consumed → a real consuming verify still succeeds once
    approvals.verify_approval_token(tok, requestor=REQ, **KW)


def test_memory_fallback_when_no_table(monkeypatch):
    monkeypatch.delenv("APPROVAL_CONSUMPTION_TABLE", raising=False)
    approvals._USED_JTIS.clear()
    tok = _mint()
    approvals.verify_approval_token(tok, requestor=REQ, **KW)
    with pytest.raises(approvals.ApprovalInvalid, match="replay"):
        approvals.verify_approval_token(tok, requestor=REQ, **KW)
