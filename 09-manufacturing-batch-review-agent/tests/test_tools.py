# tests/test_tools.py — unit tests for the Agent 09 tools + gateway policy.
import os
import sys
from pathlib import Path

os.environ.setdefault("EXTRACT_MODE", "demo")
_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "platform_core"))

from tools import exception_scanner, disposition_drafter, quality_checker


def _clean_record():
    return {
        "batch_id": "B-1", "product": "P", "required_steps": ["S1"],
        "steps": [{"id": "S1", "name": "Dispensing", "value": 100.0, "lo": 99.0, "hi": 101.0,
                   "unit": "%", "signed": True, "critical": True}],
    }


def test_scan_clean_has_no_exceptions():
    r = exception_scanner.scan(_clean_record(),
                               [{"test": "Assay", "result": 99.0, "lo": 95.0, "hi": 105.0, "status": "PASS"}])
    assert r["exception_count"] == 0 and r["critical_count"] == 0


def test_scan_flags_oos_critical():
    r = exception_scanner.scan(_clean_record(),
                               [{"test": "Assay", "result": 90.0, "lo": 95.0, "hi": 105.0, "status": "OOS"}])
    assert any(e["code"] == "OOS" and e["severity"] == "CRITICAL" for e in r["exceptions"])
    assert r["critical_count"] == 1


def test_scan_flags_out_of_limit_and_unsigned_and_missing():
    rec = {
        "batch_id": "B-2", "product": "P", "required_steps": ["S1", "S9"],
        "steps": [
            {"id": "S1", "name": "Force", "value": 20.0, "lo": 10.0, "hi": 15.0, "unit": "kN",
             "signed": False, "critical": False},
        ],
    }
    r = exception_scanner.scan(rec, [])
    codes = {e["code"] for e in r["exceptions"]}
    assert {"OUT_OF_LIMIT", "UNSIGNED_STEP", "MISSING_STEP"} <= codes


def test_drafter_demo_is_grounded_and_has_elements():
    state = {"batch_id": "B-1", "product": "Acetaminophen", "exceptions": [], "exception_count": 0,
             "critical_count": 0, "right_first_time": True}
    out = disposition_drafter.draft(state)
    assert out["report_drafted_by"] in ("demo-stub", "demo-stub-fallback")
    state["exception_report"] = out["exception_report"]
    q = quality_checker.check(state)
    assert q["required_elements_present"] is True
    assert q["grounding_report"].get("grounded", True) is True
    assert "RELEASE" in out["exception_report"]


def test_drafter_hold_when_exceptions():
    state = {"batch_id": "B-3", "product": "Amoxicillin",
             "exceptions": [{"code": "OOS", "severity": "CRITICAL", "step": "Assay",
                             "detail": "result 92 outside spec [95, 105]"}],
             "exception_count": 1, "critical_count": 1, "right_first_time": False}
    out = disposition_drafter.draft(state)
    assert "HOLD" in out["exception_report"]


# ── Gateway policy: deny-by-default + least-privilege intersection ──────────────

def test_policy_operator_can_read_but_not_record():
    from hcls_agent_platform.mcp_gateway.policy import decide
    agent = "09-manufacturing-batch-review"
    assert decide(agent, ["MFG_OPERATOR"], "mes.get_batch_record").allowed
    assert decide(agent, ["MFG_OPERATOR"], "lims.get_results").allowed
    # operator may draft but NOT record the irreversible disposition
    assert decide(agent, ["MFG_OPERATOR"], "mes.write_disposition_draft").allowed
    assert not decide(agent, ["MFG_OPERATOR"], "mes.record_disposition").allowed


def test_record_disposition_is_withheld_from_agent_but_human_entitled():
    # Phase-2: the irreversible batch release/reject is WITHHELD from the agent grant.
    # An agent can never invoke it (over-reach DENY), but the human QA_RELEASE role IS entitled.
    from hcls_agent_platform.mcp_gateway.policy import decide, user_entitlements
    d = decide("09-manufacturing-batch-review", ["QA_RELEASE"], "mes.record_disposition")
    assert not d.allowed  # agent is not granted the consequential commit
    assert "mes.record_disposition" in user_entitlements(["QA_RELEASE"])  # the human still holds it


def test_policy_agent_cannot_exceed_user():
    from hcls_agent_platform.mcp_gateway.policy import decide
    # a PV reviewer has no manufacturing entitlement -> intersection denies
    assert not decide("09-manufacturing-batch-review", ["PV_MEDICAL_REVIEWER"],
                      "mes.record_disposition").allowed
