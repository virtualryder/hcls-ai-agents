"""Tests for the connector framework (fixture mode)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcls_agent_platform.connectors import get_connector


def test_safety_fixture_roundtrip():
    conn = get_connector("safety", mode="fixture")
    assert conn.get_case(case_id="ICSR-1")["valid"] is True
    dups = conn.search_duplicates(case_id="ICSR-1")
    assert isinstance(dups, list)


def test_meddra_codes_known_term():
    conn = get_connector("meddra", mode="fixture")
    out = conn.code_term(term="nausea")
    assert out["pt"] == "Nausea" and out["pt_code"]


def test_generic_kinds_resolve():
    for kind, method in [("ctms", "get_study_status"), ("etmf", "get_completeness"),
                         ("rwd", "run_cohort_query"), ("qms", "get_complaint")]:
        conn = get_connector(kind, mode="fixture")
        assert getattr(conn, method)()


def test_live_mode_raises_not_implemented():
    conn = get_connector("safety", mode="live")
    try:
        conn.get_case(case_id="x")
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass


def test_unknown_kind_raises():
    try:
        get_connector("nope", mode="fixture")
        assert False
    except ValueError:
        pass
