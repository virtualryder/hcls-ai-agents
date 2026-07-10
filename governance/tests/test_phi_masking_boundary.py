"""PHI/PII masking boundary proof (offline) — raw identifiers survive NONE of the boundaries the
agent writes to: the model prompt, and the audit record (which feeds the DynamoDB audit table and
the S3 Object-Lock evidence export). The masker is fail-closed and applied before any model/audit
write. The *runtime* capture (a real record in a deployed DynamoDB/S3 + CloudWatch logs) is the
deploy-time proof — see 02-pharmacovigilance-agent/SECURITY-EVIDENCE-PACK.md §3 and
RUNTIME-EVIDENCE-RUNBOOK.md. This test proves the control itself, at every in-code boundary."""
import json

from hcls_agent_platform.phi import mask
from hcls_agent_platform.mcp_gateway.audit import GatewayAuditLog

# A record carrying every Safe-Harbor identifier family the masker targets.
PHI = ("Patient MRN-123456 with SSN 123-45-6789, email jane.doe@example.com, "
       "phone (555) 123-4567, DOB 1980-05-02, card 4111 1111 1111 1111, NPI 1234567893.")

# Raw substrings that MUST NOT appear downstream of the masker.
RAW = ["123-45-6789", "jane.doe@example.com", "1980-05-02", "MRN-123456",
       "123-4567", "4111 1111 1111 1111"]


def _assert_no_raw(text):
    leaked = [t for t in RAW if t in text]
    assert not leaked, f"raw PHI leaked past the masker: {leaked}"


def test_masker_removes_every_identifier_family():
    _assert_no_raw(mask(PHI))


def test_prompt_boundary_is_masked():
    # The agent masks before building any model prompt.
    prompt = f"Draft an ICSR narrative strictly from this case text:\n{mask(PHI)}"
    _assert_no_raw(prompt)


def test_audit_boundary_is_masked():
    # Anything written to the audit record (-> DynamoDB audit + S3 Object-Lock evidence) is masked.
    log = GatewayAuditLog()
    log.record({"decision": "ALLOW", "tool": "safety.get_case",
                "args": {"note": PHI, "reporter": "call from jane.doe@example.com"}})
    _assert_no_raw(json.dumps(log.records[0]))


def test_masker_is_idempotent_and_fail_closed():
    once = mask(PHI)
    assert mask(once) == once            # safe to re-apply
    assert mask(None) == ""              # never returns unmasked input


def test_real_data_mode_requires_ner_engine(monkeypatch):
    """ALLOW_REAL_DATA without an NER engine must FAIL CLOSED (names would leak)."""
    import pytest
    from hcls_agent_platform.phi import mask, RealDataMaskingError
    monkeypatch.setenv("ALLOW_REAL_DATA", "1")
    monkeypatch.delenv("MASK_ENGINE", raising=False)
    monkeypatch.delenv("PHI_ENGINE", raising=False)
    with pytest.raises(RealDataMaskingError):
        mask("Subject Jane Doe, DEA AB1234563, seen 2026-01-02")
