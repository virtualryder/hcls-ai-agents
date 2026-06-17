"""tests/test_tools.py - unit tests for all tool modules in 06-protocol-design-agent."""
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE", "demo")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_NSCLC_STATE = {
    "request_id": "PROTO-2026-001",
    "indication": "non-small cell lung cancer",
    "phase": "Phase 2",
    "therapeutic_area": "Oncology",
    "primary_objective": "evaluate progression-free survival with experimental PD-L1 inhibitor",
    "target_population": "adults with locally advanced or metastatic NSCLC, ECOG PS 0-1",
    "study_design": "Randomized Controlled Trial",
    "instructions": "Draft endpoints, eligibility, and 12-month visit schedule.",
    "guidance_hits": [
        {"ref": "ICH E9(R1)", "title": "Statistical Principles", "agency": "ICH"},
        {"ref": "ICH E6(R2)", "title": "Good Clinical Practice", "agency": "ICH"},
    ],
    "feasibility_assessment": {
        "cohort_estimate": {"total_eligible": 3240, "screened_12m": 890, "sites_with_data": 14},
        "feasibility": "FEASIBLE",
        "enrollment_target": 200,
    },
    "audit_trail": [],
    "completed_steps": [],
    "revision_count": 0,
}

_T2DM_STATE = {
    "request_id": "PROTO-2026-002",
    "indication": "type 2 diabetes mellitus",
    "phase": "Phase 3",
    "therapeutic_area": "Endocrinology",
    "primary_objective": "demonstrate superiority of investigational GLP-1 agonist on HbA1c reduction",
    "target_population": "adults aged 18-75 with type 2 diabetes mellitus, baseline HbA1c 7.5-10.5%",
    "study_design": "Randomized Controlled Trial",
    "instructions": "Draft endpoints and 52-week visit schedule.",
    "guidance_hits": [{"ref": "FDA-DIABETES-GUIDANCE", "title": "Diabetes Endpoints Guidance", "agency": "FDA"}],
    "feasibility_assessment": {
        "cohort_estimate": {"total_eligible": 18400, "screened_12m": 2100, "sites_with_data": 31},
        "feasibility": "FEASIBLE",
        "enrollment_target": 500,
    },
    "audit_trail": [],
    "completed_steps": [],
    "revision_count": 0,
}

from tools import guidance_searcher

def test_guidance_search_oncology():
    hits = guidance_searcher.search_guidance_demo("oncology progression-free survival endpoint")
    assert isinstance(hits, list) and len(hits) >= 1
    assert "ref" in hits[0] and "title" in hits[0]

def test_guidance_search_rct():
    hits = guidance_searcher.search_guidance_demo("randomized controlled trial statistical principles")
    assert isinstance(hits, list) and len(hits) >= 1

def test_guidance_search_adaptive():
    hits = guidance_searcher.search_guidance_demo("adaptive design clinical trial")
    assert isinstance(hits, list) and len(hits) >= 1

def test_guidance_search_rwd():
    hits = guidance_searcher.search_guidance_demo("real world data evidence framework")
    assert isinstance(hits, list) and len(hits) >= 1

def test_guidance_format_summary():
    hits = guidance_searcher.search_guidance_demo("clinical trial")
    summary = guidance_searcher.format_guidance_summary(hits[:2])
    assert isinstance(summary, str) and len(summary) > 10

def test_guidance_top_k():
    hits = guidance_searcher.search_guidance_demo("clinical trial endpoint", top_k=2)
    assert len(hits) <= 2

from tools import feasibility_estimator

def test_feasibility_nsclc():
    result = feasibility_estimator.estimate_cohort_demo({"indication": "non-small cell lung cancer"})
    assert result.get("total_eligible", 0) > 0
    assert result.get("sites_with_data", 0) > 0

def test_feasibility_t2dm():
    result = feasibility_estimator.estimate_cohort_demo({"indication": "type 2 diabetes mellitus"})
    assert result.get("total_eligible", 0) > 0

def test_feasibility_assessment_feasible():
    cohort = {"total_eligible": 3240, "screened_12m": 890, "sites_with_data": 14}
    assessment = feasibility_estimator.assess_feasibility(cohort, enrollment_target=200)
    assert "feasibility_rating" in assessment or "feasibility" in assessment

def test_feasibility_precedents():
    precedents = feasibility_estimator.get_study_precedents_demo("non-small cell lung cancer", "Phase 2")
    assert isinstance(precedents, list)

def test_feasibility_enrollment_rate():
    cohort = {"total_eligible": 200, "screened_12m": 50, "sites_with_data": 3}
    assessment = feasibility_estimator.assess_feasibility(cohort, enrollment_target=300)
    rating = assessment.get("feasibility_rating") or assessment.get("feasibility", "")
    assert rating in ("MARGINAL", "INFEASIBLE", "ACCEPTABLE", "FEASIBLE", "LOW") or len(rating) > 0

from tools import risk_assessor

def test_risk_assessor_operational():
    risks = risk_assessor.assess_operational_risks(dict(_NSCLC_STATE))
    assert isinstance(risks, list)

def test_risk_assessor_regulatory():
    risks = risk_assessor.assess_regulatory_risks(dict(_NSCLC_STATE))
    assert isinstance(risks, list)

def test_risk_assessor_novel_design():
    state = {**_NSCLC_STATE, "study_design": "Adaptive Seamless Design"}
    risks = risk_assessor.assess_regulatory_risks(state)
    novel = [r for r in risks if "novel" in r.lower() or "adaptive" in r.lower() or "complex" in r.lower()]
    assert len(novel) > 0, f"Expected novel design risk flag, got: {risks}"

def test_risk_assessor_no_guidance():
    state = {**_NSCLC_STATE, "guidance_hits": []}
    risks = risk_assessor.assess_regulatory_risks(state)
    no_guidance = [r for r in risks if "guidance" in r.lower() or "regulatory" in r.lower()]
    assert len(no_guidance) > 0, f"Expected no-guidance risk, got: {risks}"

def test_risk_assessor_summary():
    op_risks = risk_assessor.assess_operational_risks(dict(_NSCLC_STATE))
    reg_risks = risk_assessor.assess_regulatory_risks(dict(_NSCLC_STATE))
    summary = risk_assessor.summarize_risk_profile(op_risks, reg_risks)
    assert summary is not None and (isinstance(summary, (str, dict)))

def test_risk_assessor_t2dm():
    op_risks = risk_assessor.assess_operational_risks(dict(_T2DM_STATE))
    reg_risks = risk_assessor.assess_regulatory_risks(dict(_T2DM_STATE))
    assert isinstance(op_risks, list)
    assert isinstance(reg_risks, list)

def test_risk_surrogate_endpoint():
    state = {**_NSCLC_STATE, "phase": "Phase 3", "primary_objective": "evaluate progression-free survival as surrogate endpoint"}
    risks = risk_assessor.assess_regulatory_risks(state)
    surrogate = [r for r in risks if "surrogate" in r.lower() or "endpoint" in r.lower()]
    assert len(surrogate) > 0, f"Expected surrogate endpoint risk, got: {risks}"

from tools import protocol_drafter

def test_protocol_draft_returns_text():
    out = protocol_drafter.draft_protocol(dict(_NSCLC_STATE))
    assert "draft_protocol" in out and len(out["draft_protocol"]) > 50

def test_protocol_draft_no_ungrounded_numbers():
    import re
    out = protocol_drafter.draft_protocol(dict(_NSCLC_STATE))
    plan = out["draft_protocol"]
    nums = [int(m) for m in re.findall(r"\b(\d+)\b", plan) if int(m) > 12]
    state_text = str(_NSCLC_STATE)
    big_suspicious = [n for n in nums if n > 1000 and str(n) not in state_text]
    assert big_suspicious == [], f"Suspicious ungrounded numbers: {big_suspicious}"

def test_protocol_draft_demo_mode():
    out = protocol_drafter.draft_protocol(dict(_T2DM_STATE))
    assert "drafted_by" in out and out["drafted_by"]

from tools import protocol_checker

def test_checker_missing_elements():
    findings = protocol_checker.quality_findings("We will conduct a clinical trial.")
    assert isinstance(findings, list) and len(findings) > 0

def test_checker_complete_draft_passes():
    plan = (
        "Primary endpoint: progression-free survival measured at regular intervals.\n"
        "Secondary endpoint: overall survival.\n"
        "Eligibility: inclusion criteria for adult patients; exclusion criteria defined.\n"
        "Schedule: screening at baseline, follow-up at monthly visits.\n"
        "This draft requires review and approval by a qualified medical reviewer."
    )
    findings = protocol_checker.quality_findings(plan)
    speculative = [f for f in findings if "speculative" in f.lower() or "absolute" in f.lower()]
    assert speculative == [], f"No speculative flags expected; got: {speculative}"

def test_checker_grounding_pass():
    plan = "Primary endpoint: progression-free survival. Indication: non-small cell lung cancer."
    report = protocol_checker.grounding_findings(plan, dict(_NSCLC_STATE))
    assert "grounded" in report

def test_checker_large_number_ungrounded():
    plan = "We will enroll 99999 patients across 999 sites."
    report = protocol_checker.grounding_findings(plan, dict(_NSCLC_STATE))
    assert report.get("grounded") is False or len(report.get("ungrounded_numbers", [])) > 0
