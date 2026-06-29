"""
F3 regression: the shared connector Lambda must resolve identity/role from the
AUTHENTICATED authorizer context, never from caller-controlled request-body fields
(except in explicit local-test mode). A lower-privileged but authenticated caller
must not be able to assert a more privileged role in the body.
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
_HANDLER = _ROOT / "aws-native-reference" / "_shared" / "connector" / "handler.py"


def _load():
    spec = importlib.util.spec_from_file_location("connector_handler", _HANDLER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


handler = _load()

AUTHZ_EVENT = {
    "tool": "safety.get_case",
    # caller tries to assert a privileged role in the body…
    "identity": {"sub": "attacker", "custom:hcls_role": "QUALIFIED_PERSON"},
    # …but the authenticated authorizer says they are a low-privilege processor.
    "requestContext": {"authorizer": {"jwt": {"claims": {
        "sub": "u-real", "custom:hcls_role": "PV_PROCESSOR"}}}},
}


def test_claims_prefers_authorizer_over_body(monkeypatch):
    monkeypatch.delenv("HCLS_LOCAL_TEST", raising=False)
    claims = handler._claims(AUTHZ_EVENT)
    assert claims.get("custom:hcls_role") == "PV_PROCESSOR"  # authorizer wins
    assert claims.get("sub") == "u-real"


def test_body_identity_ignored_on_the_wire(monkeypatch):
    monkeypatch.delenv("HCLS_LOCAL_TEST", raising=False)
    # A NETWORK request always carries requestContext (added by API Gateway). With a
    # requestContext present but no usable authorizer claims, body identity must NOT be
    # trusted. (A genuine direct Lambda invoke has no requestContext and is IAM-gated.)
    claims = handler._claims({"tool": "safety.get_case",
                              "requestContext": {"http": {"method": "POST"}},
                              "identity": {"custom:hcls_role": "QUALIFIED_PERSON"}})
    assert claims == {}


def test_direct_invoke_identity_trusted(monkeypatch):
    monkeypatch.delenv("HCLS_LOCAL_TEST", raising=False)
    # No requestContext = direct (IAM-authenticated) invoke, e.g. finalize committing
    # on the approver's authority. Body identity is accepted here.
    claims = handler._claims({"tool": "safety.submit_report",
                              "identity": {"sub": "pv-physician-1", "custom:hcls_role": "PV_MEDICAL_REVIEWER"}})
    assert claims.get("sub") == "pv-physician-1"


def test_body_identity_allowed_only_in_local_test(monkeypatch):
    monkeypatch.setenv("HCLS_LOCAL_TEST", "1")
    claims = handler._claims({"tool": "safety.get_case",
                              "identity": {"custom:hcls_role": "PV_PROCESSOR"}})
    assert claims.get("custom:hcls_role") == "PV_PROCESSOR"


def test_audit_mirror_is_conditional_and_fail_closed():
    # The immutable audit writer must use a conditional (immutable) put and must not
    # swallow non-idempotent failures (round-2 #4 renamed it to _put_immutable).
    src = _HANDLER.read_text()
    assert "attribute_not_exists(audit_id)" in src
    assert "ConditionalCheckFailedException" in src
    block = src.split("def _put_immutable")[1][:900]
    assert "raise" in block
