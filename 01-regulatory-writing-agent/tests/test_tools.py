"""Unit tests for Regulatory Writing tools (demo mode, no API key)."""
import os
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))
os.environ["EXTRACT_MODE"] = "demo"

from tools import submission_drafter, consistency_checker


STATE = {
    "document_type": "BENEFIT_RISK_SUMMARY",
    "product": "Demo-Drug",
    "indication": "type 2 diabetes",
    "section_ref": "CSR STUDY-301 Section 11",
    "study_data": {
        "n_subjects": 450, "primary_endpoint": "HbA1c reduction",
        "hba1c_reduction_pct": 1.2, "comparator": "placebo",
        "source_ref": "CSR STUDY-301 Section 11", "study": "STUDY-301",
    },
    "source_documents": [{"title": "CSR", "version": "1.0", "text": "450 subjects; 1.2 pp reduction."}],
}


def test_demo_draft_is_grounded_and_clean():
    out = submission_drafter.draft_section(STATE)
    assert out["drafted_by"].startswith("demo")
    text = out["draft_text"]
    assert len(text.split()) >= 60
    findings = consistency_checker.compliance_findings(text)
    assert findings == [], f"unexpected compliance findings: {findings}"
    g = consistency_checker.grounding_findings(text, STATE)
    assert g["grounded"], f"ungrounded: {g}"


def test_compliance_flags_promotional_language():
    bad = "Demo-Drug is completely safe and a miracle cure for all patients."
    findings = consistency_checker.compliance_findings(bad)
    assert any("prohibited" in f for f in findings)


def test_grounding_flags_invented_number():
    g = consistency_checker.grounding_findings("Demo-Drug enrolled 9876 subjects.", STATE)
    assert not g["grounded"]
