"""Integration tests: Quality CAPA graph runs end-to-end in demo mode."""
import os, sys
from pathlib import Path
AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_quality_capa_graph
from agent.state import RecommendedAction


def _seed(complaint_id, event_type, severity, description, product="Demo-Parenteral",
          lot="LOT-2026-001", site="SITE-MFG-01", role="QUALIFIED_PERSON"):
    return {"request_id": f"CAPA-TEST-{complaint_id}", "complaint_id": complaint_id,
            "event_type": event_type, "product": product, "lot_number": lot, "site": site,
            "severity": severity, "description": description,
            "acting_user_claims": {"sub": "test-qa", "custom:hcls_role": role}}


_PARTICULATE_DESC = (
    "Visible particulate matter found in vial. Lot LOT-2026-001 quarantined pending investigation. "
    "Two additional complaints from same lot. Filter fiber tentatively identified."
)
_TEMP_EXCURSION_DESC = (
    "Temperature excursion in storage area. Environmental monitoring recorded 3.2 degrees above "
    "upper limit for approximately 4 hours. No product impact confirmed. HVAC maintenance overdue."
)
_STERILITY_DESC = (
    "Out-of-specification sterility test failure. Potential patient harm cannot be excluded. "
    "Regulatory reporting obligation under evaluation per 21 CFR 314.81."
)


def _run(seed):
    graph = build_quality_capa_graph(use_memory=False)
    result = None
    for event in graph.stream(seed, stream_mode="values"):
        result = event
    return result


def test_graph_runs_without_memory():
    graph = build_quality_capa_graph(use_memory=False)
    assert graph is not None

def test_graph_audit_trail_populated():
    result = _run(_seed("COMP-T01", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert len(result.get("audit_trail", [])) >= 5

def test_graph_completed_steps():
    result = _run(_seed("COMP-T02", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    steps = result.get("completed_steps", [])
    for req in ("intake", "classify_event", "search_similar_events", "root_cause_analysis", "draft_capa", "quality_check"):
        assert req in steps, f"Missing step: {req}"

def test_graph_classification_present():
    result = _run(_seed("COMP-T03", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    cls = result.get("classification", {})
    assert cls and cls.get("severity") in ("CRITICAL", "MAJOR", "MINOR")
    assert cls.get("risk_level") in ("HIGH", "MEDIUM", "LOW")

def test_graph_similar_events_present():
    result = _run(_seed("COMP-T04", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert len(result.get("similar_events", [])) >= 1

def test_graph_root_cause_hypotheses():
    result = _run(_seed("COMP-T05", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    hypotheses = result.get("root_cause_hypotheses", [])
    assert len(hypotheses) >= 1
    for h in hypotheses:
        # hypotheses may be strings or dicts depending on analyzer path
        if isinstance(h, dict):
            assert "hypothesis" in h or "category" in h
        else:
            assert isinstance(h, str) and len(h) > 0

def test_graph_capa_plan_drafted():
    result = _run(_seed("COMP-T06", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert len(result.get("capa_plan", "")) > 50

def test_graph_recommended_action_set():
    result = _run(_seed("COMP-T07", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    action = result.get("recommended_action")
    assert action is not None and isinstance(action, RecommendedAction)

def test_graph_hitl_gate_in_audit_trail():
    result = _run(_seed("COMP-T08", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    nodes = [e["node"] for e in result.get("audit_trail", [])]
    assert "human_review_gate" in nodes

def test_graph_hitl_gate_in_completed_steps():
    result = _run(_seed("COMP-T09", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert "human_review_gate" in result.get("completed_steps", [])

def test_graph_case_status_set():
    result = _run(_seed("COMP-T10", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert result.get("case_status") in ("PENDING_REVIEW", "CAPA_CREATED", "CLASSIFYING")

def test_graph_temperature_deviation():
    result = _run(_seed("COMP-T11", "TEMPERATURE_EXCURSION", "MINOR", _TEMP_EXCURSION_DESC,
                        product="Demo-Tablet", lot="LOT-2026-002", site="SITE-MFG-02"))
    cls = result.get("classification", {})
    assert cls.get("severity") in ("MINOR", "MAJOR")
    assert result.get("capa_plan")

def test_graph_grounding_report_present():
    result = _run(_seed("COMP-T12", "PRODUCT_DEFECT", "MAJOR", _PARTICULATE_DESC))
    assert "grounded" in result.get("grounding_report", {})

def test_graph_complaint_record_populated():
    result = _run(_seed("COMP-T13", "STERILITY_FAILURE", "CRITICAL", _STERILITY_DESC,
                        product="Sterile Ophthalmic Gamma", lot="LOT-2026-003"))
    rec = result.get("complaint_record", {})
    assert rec.get("complaint_id") == "COMP-T13"
