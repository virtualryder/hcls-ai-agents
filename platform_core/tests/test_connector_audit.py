"""
Round-2 #4: the connector's durable audit must (a) carry the COMPLETE evidence schema,
(b) write an immutable INTENT record BEFORE a consequential action and a COMMITTED
record (with the system-of-record response) after — the transaction boundary — and
(c) FAIL CLOSED if the outcome write fails. Plus the reconciliation core finds orphans.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM = _ROOT / "platform_core"
if str(_PLATFORM) not in sys.path:
    sys.path.insert(0, str(_PLATFORM))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


handler_mod = _load("connector_handler2", "aws-native-reference/_shared/connector/handler.py")
reconcile = _load("connector_reconcile", "aws-native-reference/_shared/connector/reconcile.py")
from hcls_agent_platform.mcp_gateway import approvals

REQ, APP = "pv-rev-1", "pv-rev-2"
ARGS = {"case_id": "ICSR-1"}


def _flatten(item):
    return {k: list(v.values())[0] for k, v in item.items()}


@pytest.fixture
def captured(monkeypatch):
    rows = []
    monkeypatch.setattr(handler_mod, "_put_immutable", lambda table, item: rows.append(_flatten(item)))
    monkeypatch.setenv("AUDIT_TABLE", "hcls-audit")
    monkeypatch.setenv("HCLS_LOCAL_TEST", "1")
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    monkeypatch.setenv("CONNECTOR_KIND", "safety")
    monkeypatch.setenv("MODEL_ID", "anthropic.claude-x")
    monkeypatch.setenv("PROMPT_VERSION", "pv-narrative-v3")
    return rows


def _consequential_event():
    token = approvals.mint_approval_token(requestor=REQ, approver=APP,
        agent_id="02-pharmacovigilance", tool="safety.write_case_draft", args=ARGS)
    return {
        "tool": "safety.write_case_draft",
        "agent_id": "02-pharmacovigilance",
        "arguments": ARGS,
        "identity": {"sub": REQ, "custom:hcls_role": "PV_MEDICAL_REVIEWER"},
        "approval": {"approved": True, "reviewer": {"sub": APP}, "token": token},
    }


def test_intent_written_before_committed(captured):
    resp = handler_mod.handler(_consequential_event())
    assert resp["decision"] == "ALLOW"
    statuses = [r["status"] for r in captured]
    assert statuses == ["INTENT", "COMMITTED"]        # ordering = transaction boundary


def test_full_evidence_schema_present(captured):
    handler_mod.handler(_consequential_event())
    outcome = [r for r in captured if r["status"] == "COMMITTED"][0]
    for field in ("audit_id", "idempotency_key", "agent_id", "tool", "user_sub", "user_role",
                  "args_hash", "decision", "allowed", "reason", "scope", "model_version",
                  "prompt_version", "approval_jti", "approver", "lineage", "sor_response"):
        assert field in outcome, f"missing evidence field: {field}"
    assert outcome["user_sub"] == REQ
    assert outcome["approver"] == APP
    assert outcome["model_version"] == "anthropic.claude-x"
    assert outcome["approval_jti"]                      # non-empty bound-token jti


def test_idempotency_key_stable_and_shared(captured):
    handler_mod.handler(_consequential_event())
    keys = {r["idempotency_key"] for r in captured}
    assert len(keys) == 1                               # intent + outcome share one key


def test_fail_closed_when_outcome_write_fails(monkeypatch):
    monkeypatch.setenv("AUDIT_TABLE", "hcls-audit")
    monkeypatch.setenv("HCLS_LOCAL_TEST", "1")
    monkeypatch.setenv("STRICT_APPROVAL", "1")
    monkeypatch.setenv("CONNECTOR_KIND", "safety")
    calls = {"n": 0}

    def boom(table, item):
        calls["n"] += 1
        if item["status"]["S"] == "COMMITTED":
            raise RuntimeError("dynamo down")

    monkeypatch.setattr(handler_mod, "_put_immutable", boom)
    with pytest.raises(RuntimeError, match="dynamo down"):
        handler_mod.handler(_consequential_event())


def test_reconcile_finds_orphan_intents():
    items = [
        {"idempotency_key": "A", "status": "INTENT", "tool": "safety.write_case_draft", "ts": "t1"},
        {"idempotency_key": "A", "status": "COMMITTED", "tool": "safety.write_case_draft", "ts": "t2"},
        {"idempotency_key": "B", "status": "INTENT", "tool": "safety.submit_report", "ts": "t3"},
    ]
    orphans = reconcile.find_orphans(items)
    assert len(orphans) == 1 and orphans[0]["idempotency_key"] == "B"
