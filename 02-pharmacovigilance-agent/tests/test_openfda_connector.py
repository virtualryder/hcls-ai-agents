"""
Tests for the openFDA (FAERS) real safety connector — Build A, task A5.

Two layers:
  * Offline/deterministic (default): monkeypatch the connector's HTTP with recorded
    real-structure cassettes. No network. These are the CI source of truth and cover
    mapping, the governed round-trip (allow reads / gate writes / withhold submit),
    duplicate detection, fail-closed writes, and fail-closed PHI masking.
  * Opt-in live smoke (RUN_LIVE_OPENFDA=1): actually calls https://api.fda.gov and
    asserts the same governed round-trip against real data. Skipped by default so CI
    needs no network.
"""
import json
import os
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))

from hcls_agent_platform.connectors import openfda  # noqa: E402
from hcls_agent_platform.connectors.factory import get_connector  # noqa: E402
from hcls_agent_platform.mcp_gateway import MCPGateway  # noqa: E402
from hcls_agent_platform.phi import mask  # noqa: E402

_FIX = AGENT / "tests" / "fixtures"
_ONE = json.loads((_FIX / "openfda_sample.json").read_text(encoding="utf-8"))
_DUPES = json.loads((_FIX / "openfda_dupes_sample.json").read_text(encoding="utf-8"))

PROCESSOR = {"sub": "u-proc", "custom:hcls_role": "PV_PROCESSOR"}


@pytest.fixture(autouse=True)
def _governed_mode(monkeypatch):
    monkeypatch.setenv("CONNECTOR_MODE", "live")
    monkeypatch.setenv("SAFETY_SOURCE", "openfda")
    monkeypatch.delenv("STRICT_APPROVAL", raising=False)


def _serve(monkeypatch, payload):
    """Monkeypatch the connector's HTTP layer to return a cassette (offline)."""
    monkeypatch.setattr(openfda.OpenFDASafetyConnector, "_get", lambda self, params: payload)


# ── Mapping ──────────────────────────────────────────────────────────────────

def test_maps_real_faers_record_to_icsr_shape():
    rec = openfda.OpenFDASafetyConnector._map_report(_ONE["results"][0])
    assert rec["case_id"] == "18424955"
    assert rec["valid"] is True and rec["status"] == "OPEN"
    assert rec["serious"] is True and "Hospitalization" in rec["seriousness_criteria"]
    assert rec["suspect_drugs"] == ["METFORMIN"]
    assert "Lactic acidosis" in rec["reactions"] and "Acute kidney injury" in rec["reactions"]
    assert rec["demographics"]["sex"] == "Female" and rec["demographics"]["age"] == "67 year"
    # narrative claims only what the record contains (grounding-friendly for Build B)
    assert "METFORMIN" in rec["narrative_text"] and "18424955" in rec["narrative_text"]


def test_get_case_returns_icsr_shape(monkeypatch):
    _serve(monkeypatch, _ONE)
    c = openfda.OpenFDASafetyConnector()
    rec = c.get_case(case_id="18424955")
    assert rec["case_id"] == "18424955" and rec["serious"] is True


# ── Duplicate detection (positive match, 2-case cassette) ────────────────────

def test_search_duplicates_positive_match(monkeypatch):
    _serve(monkeypatch, _DUPES)
    c = openfda.OpenFDASafetyConnector()
    dups = c.search_duplicates(suspect_drug="METFORMIN", meddra_pt="Lactic acidosis",
                               case_id="18424955")
    assert len(dups) == 1
    assert dups[0]["case_id"] == "18500001"          # the OTHER case, query case excluded
    assert dups[0]["match_score"] == 1.0             # shared drug (0.5) + reaction (0.5)


def test_search_duplicates_requires_criteria(monkeypatch):
    _serve(monkeypatch, _DUPES)
    assert openfda.OpenFDASafetyConnector().search_duplicates() == []


# ── Writes are fail-closed (read-only public source) ─────────────────────────

def test_write_case_draft_raises():
    with pytest.raises(NotImplementedError):
        openfda.OpenFDASafetyConnector().write_case_draft(case_id="X")


def test_submit_report_raises():
    with pytest.raises(NotImplementedError):
        openfda.OpenFDASafetyConnector().submit_report(case_id="X")


# ── Factory routing ──────────────────────────────────────────────────────────

def test_factory_routes_to_openfda():
    assert type(get_connector("safety")).__name__ == "OpenFDASafetyConnector"


# ── Governed round-trip through the real gateway ─────────────────────────────

def test_governed_reads_allowed_writes_gated_submit_withheld(monkeypatch):
    _serve(monkeypatch, _ONE)
    gw = MCPGateway()
    read = gw.invoke(user_claims=PROCESSOR, agent_id="02-pharmacovigilance",
                     tool="safety.get_case", args={"case_id": "18424955"})
    assert read.allowed and read.decision == "ALLOW"
    assert read.result["case_id"] == "18424955" and read.audit_id
    assert read.scope == ["safety.get_case"]

    dup = gw.invoke(user_claims=PROCESSOR, agent_id="02-pharmacovigilance",
                    tool="safety.search_duplicates",
                    args={"suspect_drug": "METFORMIN", "meddra_pt": "Lactic acidosis"})
    assert dup.allowed

    write = gw.invoke(user_claims=PROCESSOR, agent_id="02-pharmacovigilance",
                      tool="safety.write_case_draft", args={"case_id": "18424955"})
    assert not write.allowed and write.requires_approval  # human-gated

    submit = gw.invoke(user_claims=PROCESSOR, agent_id="02-pharmacovigilance",
                       tool="safety.submit_report", args={"case_id": "18424955"})
    assert not submit.allowed and submit.decision == "DENY"  # withheld from the agent


def test_least_privilege_denies_unentitled_role(monkeypatch):
    _serve(monkeypatch, _ONE)
    gw = MCPGateway()
    r = gw.invoke(user_claims={"sub": "x", "custom:hcls_role": "MSL"},
                  agent_id="02-pharmacovigilance", tool="safety.get_case",
                  args={"case_id": "18424955"})
    assert not r.allowed and r.decision == "DENY"


# ── A3: fail-closed PHI masking on ingested text ─────────────────────────────

def test_phi_masking_failclosed_on_ingested_text(monkeypatch):
    _serve(monkeypatch, _ONE)
    rec = openfda.OpenFDASafetyConnector().get_case(case_id="18424955")
    # openFDA is de-identified; stress the control with injected identifiers.
    stressed = rec["narrative_text"] + " reporter jane.doe@example.com SSN 123-45-6789"
    masked = mask(stressed)
    assert "123-45-6789" not in masked
    assert "jane.doe@example.com" not in masked


# ── Opt-in live smoke against the real openFDA API ───────────────────────────

@pytest.mark.skipif(os.getenv("RUN_LIVE_OPENFDA", "") not in ("1", "true", "yes"),
                    reason="set RUN_LIVE_OPENFDA=1 to hit the real api.fda.gov")
def test_live_openfda_governed_read():
    gw = MCPGateway()
    r = gw.invoke(user_claims=PROCESSOR, agent_id="02-pharmacovigilance",
                  tool="safety.get_case", args={})   # most-recent serious case
    assert r.allowed and r.result.get("valid") is True
    assert r.result.get("case_id")            # a real FAERS report id
    assert r.audit_id                         # audited
