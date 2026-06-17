"""Tests for platform primitives: PHI masking, secrets, auth, tracing."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcls_agent_platform import mask, luhn_valid, get_secret, traced_node
from hcls_agent_platform import auth


def test_mask_redacts_phi_identifiers():
    text = "Patient SUBJ-00123 SSN 123-45-6789 emailed jane@acme.com on 2026-01-04, MRN 998877665"
    out = mask(text)
    assert "123-45-6789" not in out
    assert "jane@acme.com" not in out
    assert "SUBJ-00123" not in out
    assert "2026-01-04" not in out
    assert "998877665" not in out
    assert "[SSN-REDACTED]" in out


def test_mask_idempotent_and_none_safe():
    assert mask(None) == ""
    once = mask("SSN 123-45-6789")
    assert mask(once) == once


def test_luhn_valid_card_detection():
    assert luhn_valid("4111111111111111")  # test Visa
    assert not luhn_valid("4111111111111112")


def test_card_masked_only_when_luhn_valid():
    assert "[CARD-REDACTED]" in mask("card 4111 1111 1111 1111")


def test_get_secret_env_first(monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "abc")
    monkeypatch.setenv("DISABLE_SECRETS_MANAGER", "1")
    assert get_secret("my_token") == "abc"
    assert get_secret("missing", default="d") == "d"


def test_auth_verify_requires_sub():
    try:
        auth.verify_jwt({"name": "no sub"})
        assert False, "expected AuthError"
    except auth.AuthError:
        pass
    claims = auth.verify_jwt({"sub": "u1", "custom:hcls_role": "PV_PROCESSOR"})
    assert claims["sub"] == "u1"


def test_require_role_and_reviewer_record():
    claims = {"sub": "u1", "custom:hcls_role": ["PV_MEDICAL_REVIEWER"]}
    assert auth.require_role(claims, ["PV_MEDICAL_REVIEWER"]) == "PV_MEDICAL_REVIEWER"
    rec = auth.record_reviewer_identity(claims, "approve", "Approved SAE causality assessment")
    assert rec["approved"] is True and rec["reviewer"]["sub"] == "u1"
    assert rec["signature_meaning"].startswith("Approved")


def test_traced_node_passthrough():
    @traced_node("demo")
    def f(x):
        return x * 2
    assert f(21) == 42
