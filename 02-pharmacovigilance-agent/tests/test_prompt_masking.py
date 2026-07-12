"""B1: PII/PHI is masked BEFORE the model sees the narrative prompt, fail-closed.

Proves the hero pipeline (tools/narrative_drafter.draft_narrative) runs the masker on
the assembled prompt before llm.invoke, and that real-data mode is fail-closed (a NER
failure blocks the draft rather than sending raw PHI to the model)."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))

import pytest
from hcls_agent_platform.pii_masker import mask, RealDataMaskingError
from tools.narrative_drafter import draft_narrative

_RAW_SSN = "123-45-6789"
_RAW_EMAIL = "jane.reporter@example.org"


def test_masker_redacts_structured_identifiers(monkeypatch):
    r = mask(f"Reporter SSN {_RAW_SSN}, email {_RAW_EMAIL}, phone 312-555-0142, DOB 1980-01-02.")
    assert r.changed
    assert _RAW_SSN not in r.text and _RAW_EMAIL not in r.text
    assert "[PII:SSN]" in r.text and "[PII:EMAIL]" in r.text
    assert "PII:SSN" in r.entity_types and "PII:PHONE" in r.entity_types

    # Regex ID pass tuned to real-world MRN/account/member/patient label variants (not just "MRN:").
    for raw, ident in [
        ("MR# 12-345678", "12-345678"),
        ("Patient ID: A0093281", "A0093281"),
        ("Member No 55521234", "55521234"),
        ("medical record number 0098213", "0098213"),
        ("Acct #: 4471209", "4471209"),
    ]:
        m = mask(f"Admission note — {raw} — severe headache.")
        assert ident not in m.text, f"{raw!r} left the id {ident!r} in the clear"
        assert "[PII:MRN]" in m.text

    # A bare all-digit run is NOT masked by default (avoids false positives on quantities/doses)...
    assert mask("Dispensed 12345678 units").changed is False
    # ...until a site injects its own bare MRN format via HCLS_MRN_PATTERNS (site-tunable, no code change).
    monkeypatch.setenv("HCLS_MRN_PATTERNS", r"\b\d{8}\b")
    sited = mask("Epic MRN on the chart is 12345678 for this case")
    assert "12345678" not in sited.text and "[PII:MRN]" in sited.text


class _FakeResp:
    content = "drafted narrative"


class _FakeLLM:
    def __init__(self):
        self.seen = None

    def invoke(self, messages):
        self.seen = messages
        return _FakeResp()


def _state():
    return {
        "patient_age": "67",
        "patient_sex": "male",
        "suspect_drug": "Examplezumab",
        # raw identifiers land in a free-text field that flows into the prompt:
        "event_description": f"Reporter SSN {_RAW_SSN}, contact {_RAW_EMAIL}. Severe headache.",
        "event_outcome": "RECOVERED",
    }


def test_prompt_is_masked_before_invoke(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")   # non-demo path
    monkeypatch.delenv("EXTRACT_MODE", raising=False)
    monkeypatch.delenv("MASK_NER", raising=False)
    monkeypatch.delenv("ALLOW_REAL_DATA", raising=False)
    fake = _FakeLLM()
    import hcls_agent_platform
    monkeypatch.setattr(hcls_agent_platform, "get_llm", lambda *a, **k: fake)

    out = draft_narrative(_state())

    # the model was called with a MASKED human prompt — raw SSN/email never reached it
    assert fake.seen is not None, "llm.invoke was not called"
    human = "".join(str(m) for m in fake.seen)
    assert _RAW_SSN not in human and _RAW_EMAIL not in human
    assert "[PII:SSN]" in human
    assert out.get("prompt_masked") is True
    assert "PII:SSN" in (out.get("masked_entity_types") or "")


def test_real_data_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.delenv("EXTRACT_MODE", raising=False)
    monkeypatch.setenv("ALLOW_REAL_DATA", "1")       # mandatory-NER real-data mode
    # simulate the NER engine being unavailable:
    import hcls_agent_platform.pii_masker as pm
    def _boom(_text):
        raise RuntimeError("comprehend unreachable")
    monkeypatch.setattr(pm, "_ner_spans", _boom)
    fake = _FakeLLM()
    import hcls_agent_platform
    monkeypatch.setattr(hcls_agent_platform, "get_llm", lambda *a, **k: fake)

    with pytest.raises(RealDataMaskingError):
        draft_narrative(_state())
    # fail-closed: the model was NEVER called
    assert fake.seen is None
