"""tests/test_tools.py - unit tests for all tool modules in 05-quality-capa-agent."""
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ.setdefault("EXTRACT_MODE", "demo")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_PARTICULATE_DESC = (
    "Visible particulate matter observed in 3 vials from lot LOT-2026-001 "
    "of Sterile Injectable Alpha during incoming QC inspection at SITE-MFG-01."
)
_TEMPERATURE_DESC = (
    "Temperature excursion recorded during cold-chain storage: "
    "12 hours at 9 degrees C instead of required 2-8 degrees C."
)
_STERILITY_DESC = (
    "Sterility test out-of-specification result: microbial growth in "
    "2 of 10 units tested. Regulatory reporting under 21 CFR 314.81."
)
_CRITICAL_STATE = {
    "complaint_id": "COMP-2026-003", "product": "Sterile Ophthalmic Gamma",
    "lot_number": "LOT-2026-003", "site": "SITE-MFG-01",
    "event_type": "STERILITY_FAILURE", "severity": "CRITICAL",
    "description": _STERILITY_DESC,
    "classification": {"severity": "CRITICAL", "risk_level": "HIGH", "regulatory_reporting_required": True,
                       "event_type": "sterility_failure", "ishikawa_categories": ["method", "measurement"], "recurrence_risk": "HIGH"},
    "similar_events": [{"id": "COMP-2025-007", "description": "sterility OOS", "score": 0.91}],
    "root_cause_hypotheses": [{"category": "method", "hypothesis": "filtration integrity failure", "confidence": 0.82}],
    "audit_trail": [], "completed_steps": [], "revision_count": 0,
}
_MAJOR_STATE = {
    "complaint_id": "COMP-2026-001", "product": "Sterile Injectable Alpha",
    "lot_number": "LOT-2026-001", "site": "SITE-MFG-01",
    "event_type": "PRODUCT_DEFECT", "severity": "MAJOR",
    "description": _PARTICULATE_DESC,
    "classification": {"severity": "MAJOR", "risk_level": "MEDIUM", "regulatory_reporting_required": False,
                       "event_type": "product_defect", "ishikawa_categories": ["material", "environment"], "recurrence_risk": "MEDIUM"},
    "similar_events": [{"id": "COMP-2025-003", "description": "particulate in vial", "score": 0.87}],
    "root_cause_hypotheses": [{"category": "material", "hypothesis": "filter degradation during filling", "confidence": 0.78}],
    "audit_trail": [], "completed_steps": [], "revision_count": 0,
}

from tools import complaint_classifier

def test_classify_major_particulate():
    r = complaint_classifier.classify(_PARTICULATE_DESC, "MAJOR", "PRODUCT_DEFECT")
    assert r["severity"] == "MAJOR"
    assert r["risk_level"] in ("MEDIUM", "HIGH")
    assert isinstance(r["regulatory_reporting_required"], bool)

def test_classify_critical_sterility():
    r = complaint_classifier.classify(_STERILITY_DESC, "CRITICAL", "STERILITY_FAILURE")
    assert r["severity"] == "CRITICAL"
    assert r["risk_level"] == "HIGH"
    assert r["regulatory_reporting_required"] is True

def test_classify_minor_temperature():
    r = complaint_classifier.classify(_TEMPERATURE_DESC, "MINOR", "TEMPERATURE_EXCURSION")
    assert r["severity"] in ("MINOR", "MAJOR")
    assert isinstance(r["regulatory_reporting_required"], bool)

def test_classify_returns_event_type():
    r = complaint_classifier.classify(_PARTICULATE_DESC, "", "")
    assert "event_type" in r and r["event_type"]

def test_classify_batch_returns_list():
    events = [{"description": _PARTICULATE_DESC, "severity": "MAJOR", "event_type": ""},
              {"description": _STERILITY_DESC, "severity": "CRITICAL", "event_type": ""}]
    results = complaint_classifier.classify_batch(events)
    assert isinstance(results, list) and len(results) == 2

from tools import similarity_search

def test_search_similar_demo_particulate():
    results = similarity_search.search_similar_demo({"product": "injectable", "event_type": "PRODUCT_DEFECT", "description": "particulate matter"})
    assert isinstance(results, list) and len(results) >= 1
    assert "score" in results[0] and results[0]["score"] <= 1.0

def test_search_similar_demo_temperature():
    results = similarity_search.search_similar_demo({"product": "biologic", "event_type": "TEMPERATURE_EXCURSION", "description": "temperature excursion"})
    assert isinstance(results, list) and len(results) >= 1

def test_search_similar_scores_ordered():
    results = similarity_search.search_similar_demo({"description": "particulate vial sterile"})
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_cluster_events_returns_clusters():
    events = [
        {"id": "E1", "description": "particulate", "score": 0.91, "root_cause": "filter integrity test skipped"},
        {"id": "E2", "description": "particulate fibers", "score": 0.87, "root_cause": "filter not tested"},
        {"id": "E3", "description": "temperature excursion", "score": 0.79, "root_cause": "hvac alarm threshold"},
    ]
    clusters = similarity_search.cluster_events(events)
    assert isinstance(clusters, list) and len(clusters) >= 1
    for c in clusters:
        assert "cluster_id" in c and "count" in c

from tools import root_cause_analyzer

def test_rca_returns_hypotheses():
    result = root_cause_analyzer.analyze(description=_PARTICULATE_DESC,
        similar_events=[{"id": "E1", "description": "particulate", "score": 0.91}],
        clusters=[{"cluster_id": "CLU-FILTER", "theme": "filtration", "count": 3}])
    assert "root_cause_hypotheses" in result and len(result["root_cause_hypotheses"]) >= 1

def test_rca_has_ishikawa_categories():
    result = root_cause_analyzer.analyze(description=_STERILITY_DESC, similar_events=[], clusters=[])
    cats = result["ishikawa_categories"]
    assert isinstance(cats, list)
    known = {"method", "machine", "material", "man", "environment", "measurement"}
    for c in cats:
        assert c in known, f"Unknown Ishikawa category: {c}"

def test_rca_recurrence_risk_present():
    result = root_cause_analyzer.analyze(description=_TEMPERATURE_DESC,
        similar_events=[{"id": "E1", "description": "temperature", "score": 0.88}], clusters=[])
    assert result["recurrence_risk"] in ("LOW", "MEDIUM", "HIGH")

from tools import capa_drafter

def test_capa_draft_returns_plan():
    out = capa_drafter.draft_capa(dict(_MAJOR_STATE))
    assert "capa_plan" in out and len(out["capa_plan"]) > 50

def test_capa_draft_no_ungrounded_large_numbers():
    import re
    out = capa_drafter.draft_capa(dict(_MAJOR_STATE))
    plan = out["capa_plan"]
    nums = [int(m) for m in re.findall(r"\b(\d+)\b", plan) if int(m) > 12]
    state_text = str(_MAJOR_STATE)
    big_suspicious = [n for n in nums if n > 100 and str(n) not in state_text]
    assert big_suspicious == [], f"Suspicious ungrounded numbers: {big_suspicious}"

def test_capa_draft_demo_mode():
    out = capa_drafter.draft_capa(dict(_CRITICAL_STATE))
    assert "drafted_by" in out and out["drafted_by"]

from tools import quality_checker

def test_quality_findings_missing_element():
    findings = quality_checker.quality_findings("We will investigate the root cause.")
    assert isinstance(findings, list) and len(findings) > 0

def test_quality_findings_speculative():
    plan = ("Corrective action: replace the filter. "
            "This might work and could possibly eliminate the issue. "
            "Effectiveness check: inspect lot LOT-2026-001 within 30 days.")
    findings = quality_checker.quality_findings(plan)
    speculative = [f for f in findings if "speculative" in f.lower() or "hedging" in f.lower()]
    assert len(speculative) > 0, f"Expected speculative language flag, got: {findings}"

def test_quality_findings_complete_plan_passes():
    plan = (
        "Root cause: filter integrity failure detected during production run.\n"
        "Corrective action: replace all integrity-test-failed filters with validated units.\n"
        "Preventive action: implement monthly filter integrity qualification protocol.\n"
        "Effectiveness check: zero particulate complaints from next 3 lots within 90 days.\n"
        "Regulatory obligation: MDR report filed within 30 days per 21 CFR 803.\n"
        "Responsible owner: QA Director, Site SITE-MFG-01.\n"
        "Target completion: within 60 days of CAPA initiation date.\n"
        "This draft requires qualified person review and approval."
    )
    findings = quality_checker.quality_findings(plan)
    speculative = [f for f in findings if "speculative" in f.lower() or "hedging" in f.lower()]
    assert speculative == [], f"No speculative flags expected; got: {speculative}"

def test_grounding_findings_pass():
    report = quality_checker.grounding_findings("Lot LOT-2026-001 particulate matter in 3 vials.", dict(_MAJOR_STATE))
    assert "grounded" in report

def test_grounding_findings_large_number_ungrounded():
    report = quality_checker.grounding_findings("We observed 9999 defects in the batch.", dict(_MAJOR_STATE))
    assert report.get("grounded") is False or len(report.get("ungrounded_numbers", [])) > 0
