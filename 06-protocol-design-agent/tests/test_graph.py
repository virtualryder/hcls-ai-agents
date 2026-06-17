"""Integration tests: Protocol Design graph runs end-to-end in demo mode."""
import os, sys
from pathlib import Path
AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from agent.graph import build_protocol_design_graph
from agent.state import RecommendedAction


def _seed(req_id, indication, phase, objective, population="adults", design="Randomized Controlled Trial", role="MEDICAL_REVIEWER"):
    return {"request_id": req_id, "indication": indication, "phase": phase,
            "therapeutic_area": "Oncology", "primary_objective": objective,
            "target_population": population, "study_design": design,
            "instructions": "Draft endpoints, eligibility, and visit schedule.",
            "acting_user_claims": {"sub": "test-reviewer", "custom:hcls_role": role}}


_NSCLC_OBJ = "evaluate progression-free survival with experimental PD-L1 inhibitor versus chemotherapy"
_T2DM_OBJ = "demonstrate superiority of investigational GLP-1 agonist on HbA1c reduction"


def _run(seed):
    graph = build_protocol_design_graph(use_memory=False)
    result = None
    for event in graph.stream(seed, stream_mode="values"):
        result = event
    return result


def test_graph_runs_without_memory():
    graph = build_protocol_design_graph(use_memory=False)
    assert graph is not None

def test_graph_audit_trail_populated():
    result = _run(_seed("PROTO-T01", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert len(result.get("audit_trail", [])) >= 1

def test_graph_completed_steps():
    result = _run(_seed("PROTO-T02", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    steps = result.get("completed_steps", [])
    for req in ("intake", "search_guidance", "feasibility_estimate", "draft_protocol_sections", "risk_assessment", "quality_check"):
        assert req in steps, f"Missing: {req}"

def test_graph_guidance_hits_present():
    result = _run(_seed("PROTO-T03", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert len(result.get("guidance_hits", [])) >= 1

def test_graph_cohort_estimate_present():
    result = _run(_seed("PROTO-T04", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ,
                        population="adults with NSCLC"))
    fa = result.get("feasibility_assessment", {})
    assert fa, "feasibility_assessment must be populated"
    # total_eligible may be at top level or nested under cohort_estimate
    total = fa.get("total_eligible") or fa.get("cohort_estimate", {}).get("total_eligible", 0)
    assert total > 0

def test_graph_feasibility_assessed():
    result = _run(_seed("PROTO-T05", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    fa = result.get("feasibility_assessment", {})
    rating_key = "feasibility_rating" if "feasibility_rating" in fa else "feasibility"
    assert rating_key in fa
    assert fa[rating_key] in ("FEASIBLE", "MARGINAL", "INFEASIBLE", "ACCEPTABLE", "LOW")

def test_graph_draft_protocol_present():
    result = _run(_seed("PROTO-T06", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert len(result.get("draft_protocol", "")) > 50

def test_graph_recommended_action_set():
    result = _run(_seed("PROTO-T07", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    action = result.get("recommended_action")
    assert action is not None and isinstance(action, RecommendedAction)

def test_graph_hitl_gate_in_audit_trail():
    result = _run(_seed("PROTO-T08", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    nodes = [e["node"] for e in result.get("audit_trail", [])]
    assert "human_review_gate" in nodes or "human_review_gate" in result.get("completed_steps", [])

def test_graph_hitl_gate_in_completed_steps():
    result = _run(_seed("PROTO-T09", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert "human_review_gate" in result.get("completed_steps", [])

def test_graph_protocol_status_set():
    result = _run(_seed("PROTO-T10", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert result.get("protocol_status") in ("PENDING_REVIEW", "SUBMITTED", "DRAFT", "IN_PROGRESS", "ANALYZING") or result.get("case_status") in ("PENDING_REVIEW", "ANALYZING", "DRAFT")

def test_graph_t2dm_phase3():
    result = _run(_seed("PROTO-T11", "type 2 diabetes mellitus", "Phase 3", _T2DM_OBJ,
                        population="adults with type 2 diabetes mellitus", design="Randomized Controlled Trial"))
    assert result.get("draft_protocol")
    fa = result.get("feasibility_assessment", {})
    total = fa.get("total_eligible") or fa.get("cohort_estimate", {}).get("total_eligible", 0)
    assert total > 0

def test_graph_grounding_report_present():
    result = _run(_seed("PROTO-T12", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert "grounded" in result.get("grounding_report", {})

def test_graph_risk_assessment_present():
    result = _run(_seed("PROTO-T13", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert "operational_risks" in result or "regulatory_risks" in result

def test_graph_quality_findings_present():
    result = _run(_seed("PROTO-T14", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert "quality_findings" in result

def test_graph_request_id_preserved():
    result = _run(_seed("PROTO-T15", "non-small cell lung cancer", "Phase 2", _NSCLC_OBJ))
    assert result.get("request_id") == "PROTO-T15"
