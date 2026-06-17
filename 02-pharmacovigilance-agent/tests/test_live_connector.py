"""
Live connector tests — real HTTP round-trip to the local reference safety service.

Starts reference_safety_service on an ephemeral port, sets SAFETY_BASE_URL +
CONNECTOR_MODE=live, and asserts every SafetyConnector method returns the
correct shape from an actual HTTP request. No mocking, no fixtures — this
proves the LiveSafetyConnector path works end-to-end without AWS credentials.

These tests are safe to run in CI: the service starts and stops in-process,
uses only stdlib, and binds to 127.0.0.1:0 (OS-assigned ephemeral port).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure platform_core and agent are importable
REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

# Start the reference service BEFORE importing the connector so SAFETY_BASE_URL
# is available to the factory. We set env vars at module load time.
from demo.reference_safety_service import start_in_background, stop, reset_store

_PORT: int = 0


def setup_module(module: object) -> None:
    global _PORT
    _PORT = start_in_background(port=0)
    os.environ["SAFETY_BASE_URL"] = f"http://127.0.0.1:{_PORT}"
    os.environ["CONNECTOR_MODE"] = "live"
    os.environ["DISABLE_SECRETS_MANAGER"] = "1"  # no AWS needed for tests


def teardown_module(module: object) -> None:
    stop()
    # Restore env to not affect other test modules
    os.environ.pop("SAFETY_BASE_URL", None)
    os.environ.pop("CONNECTOR_MODE", None)
    os.environ.pop("DISABLE_SECRETS_MANAGER", None)


def setup_function(function: object) -> None:
    reset_store()


# ---------------------------------------------------------------------------
# Helper — get a fresh LiveSafetyConnector pointing at the local service
# ---------------------------------------------------------------------------

def _connector():
    # Import after env vars are set
    from hcls_agent_platform.connectors.factory import get_connector
    return get_connector("safety", mode="live")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_connector_is_live_safety():
    """Factory returns LiveSafetyConnector (not the fixture) when SAFETY_BASE_URL is set."""
    from hcls_agent_platform.connectors.live import LiveSafetyConnector
    conn = _connector()
    assert isinstance(conn, LiveSafetyConnector), (
        f"Expected LiveSafetyConnector, got {type(conn).__name__}"
    )


def test_get_case_known_id():
    """GET /cases/ICSR-2026-0001 returns the stored case with correct shape."""
    conn = _connector()
    result = conn.get_case(case_id="ICSR-2026-0001")

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert result.get("case_id") == "ICSR-2026-0001"
    assert result.get("status") == "OPEN"
    assert result.get("valid") is True
    assert result.get("suspect_drug") == "Metformin"


def test_get_case_serious_id():
    """GET /cases/ICSR-2026-0002 returns the hospitalization case."""
    conn = _connector()
    result = conn.get_case(case_id="ICSR-2026-0002")

    assert result["case_id"] == "ICSR-2026-0002"
    assert result["is_serious"] is True
    assert "hospitalization" in result.get("seriousness_criteria", [])


def test_get_case_unknown_id_returns_placeholder():
    """Unknown case IDs return a placeholder dict (not 404 error)."""
    conn = _connector()
    result = conn.get_case(case_id="ICSR-UNKNOWN-9999")

    assert isinstance(result, dict)
    assert result.get("case_id") == "ICSR-UNKNOWN-9999"
    assert result.get("valid") is True  # factory normalises


def test_search_duplicates_high_overlap():
    """POST /cases/search-duplicates returns match when drug + event overlap."""
    conn = _connector()
    criteria = {
        "suspect_drug": "Lisinopril",
        "meddra_pt": "renal failure",
        "reporter_country": "Canada",
    }
    matches = conn.search_duplicates(**criteria)

    assert isinstance(matches, list), f"Expected list, got {type(matches)}"
    # The Lisinopril case (ICSR-2026-0002) overlaps on drug, event, and country
    assert len(matches) >= 1, f"Expected at least one duplicate match; got {matches}"
    match = matches[0]
    assert "case_id" in match, f"match missing case_id: {match}"
    assert "match_score" in match, f"match missing match_score: {match}"
    assert match["match_score"] >= 0.5, (
        f"match_score should be >=0.5 for a strong overlap; got {match['match_score']}"
    )


def test_search_duplicates_no_overlap():
    """POST /cases/search-duplicates returns empty list for an unrelated case."""
    conn = _connector()
    criteria = {
        "suspect_drug": "CompletlyUnknownDrugXYZ",
        "meddra_pt": "extremely_rare_event_xyz",
        "reporter_country": "Antarctica",
    }
    matches = conn.search_duplicates(**criteria)

    assert isinstance(matches, list)
    # No stored case should match this fictional drug/event
    assert len(matches) == 0, (
        f"Expected no duplicates for unrelated drug; got {matches}"
    )


def test_search_duplicates_returns_list():
    """search_duplicates always returns a list even with empty criteria."""
    conn = _connector()
    result = conn.search_duplicates()

    assert isinstance(result, list)


def test_write_case_draft_returns_draft_id():
    """POST /cases/drafts returns a draft case_id and DRAFT status."""
    conn = _connector()
    payload = {
        "case_id": "ICSR-TEST-DRAFT-001",
        "patient_age": "52 years",
        "suspect_drug": "Metformin",
        "meddra_pt": "Nausea",
        "is_serious": False,
        "narrative_text": "Test narrative for draft.",
    }
    result = conn.write_case_draft(**payload)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "case_id" in result, f"write_case_draft missing case_id: {result}"
    # The reference service generates a new ID prefixed ICSR-DRAFT-
    assert result["case_id"].startswith("ICSR-DRAFT-"), (
        f"Expected ICSR-DRAFT-... ID; got {result['case_id']}"
    )
    assert result.get("status") == "DRAFT"
    assert result.get("written") is True


def test_write_case_draft_persists():
    """A draft written via POST /cases/drafts can be retrieved via GET /cases/{id}."""
    conn = _connector()
    draft_result = conn.write_case_draft(patient_age="67 years", suspect_drug="Warfarin")
    draft_id = draft_result["case_id"]

    # Retrieve the draft (reference service stores drafts in-memory)
    retrieved = conn.get_case(case_id=draft_id)
    assert retrieved.get("case_id") == draft_id


def test_submit_report_returns_submission_id():
    """POST /reports returns a submission_id and QUEUED status (E2B gateway style)."""
    conn = _connector()
    payload = {
        "case_id": "ICSR-2026-0002",
        "meddra_pt": "Renal failure acute",
        "suspect_drug": "Lisinopril",
        "is_serious": True,
        "gateway": "FDA-FAERS",
        "narrative_len": 512,
    }
    result = conn.submit_report(**payload)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "submission_id" in result, f"submit_report missing submission_id: {result}"
    assert result["submission_id"].startswith("E2B-"), (
        f"Expected E2B-... ID; got {result['submission_id']}"
    )
    assert result.get("status") == "QUEUED"
    assert result.get("gateway") == "FDA-FAERS-E2B"


def test_fixture_mode_unchanged():
    """Fixture mode is completely unaffected by live path changes."""
    # Temporarily override CONNECTOR_MODE to fixture
    original = os.environ.get("CONNECTOR_MODE", "live")
    os.environ["CONNECTOR_MODE"] = "fixture"
    try:
        from hcls_agent_platform.connectors.factory import get_connector
        from hcls_agent_platform.connectors.fixtures import FixtureSafety
        conn = get_connector("safety", mode="fixture")
        assert isinstance(conn, FixtureSafety)
        result = conn.get_case(case_id="ICSR-1")
        assert result["valid"] is True
        dups = conn.search_duplicates()
        assert isinstance(dups, list)
        assert dups[0]["match_score"] == 0.34  # fixture always returns 0.34
    finally:
        os.environ["CONNECTOR_MODE"] = original


def test_meddra_whodrug_remain_fixture_in_live_mode():
    """In live mode, MedDRA and WHODrug still use fixture connectors (licensed API)."""
    from hcls_agent_platform.connectors.factory import get_connector
    from hcls_agent_platform.connectors.fixtures import FixtureMedDRA, FixtureWHODrug

    meddra = get_connector("meddra", mode="live")
    assert isinstance(meddra, FixtureMedDRA)

    whodrug = get_connector("whodrug", mode="live")
    assert isinstance(whodrug, FixtureWHODrug)


def test_health_endpoint():
    """The /health endpoint returns ok (smoke test for the reference service itself)."""
    import urllib.request
    with urllib.request.urlopen(f"http://127.0.0.1:{_PORT}/health", timeout=5) as resp:
        body = resp.read().decode("utf-8")
    import json
    data = json.loads(body)
    assert data.get("status") == "ok"
