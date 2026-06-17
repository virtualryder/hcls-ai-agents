# tools/tmf_analyzer.py
from __future__ import annotations
from typing import Any, Dict, List

# ICH E6(R2) truly inspection-critical sections
_CRITICAL_SECTIONS = {
    "Protocol",
    "Investigator Brochure",
    "IRB Correspondence",
    "IRB Approval",
    "Informed Consent",
    "Regulatory Approval",
    "Randomization List",
    "Blinding Document",
}

# Major but not immediately critical
_MAJOR_SECTIONS = {
    "Site Activation",
    "Site Activation Log",
    "Laboratory Certification",
    "CRF Completion",
    "Training Record",
    "Monitoring Visit",
}


def _classify_document(doc_name: str) -> str:
    for kw in _CRITICAL_SECTIONS:
        if kw.lower() in doc_name.lower():
            return "CRITICAL"
    for kw in _MAJOR_SECTIONS:
        if kw.lower() in doc_name.lower():
            return "MAJOR"
    return "MINOR"


def analyze(tmf_data: Dict[str, Any]) -> Dict[str, Any]:
    pct = tmf_data.get("completeness_pct", 0)
    missing = tmf_data.get("missing_documents", [])
    last_reviewed = tmf_data.get("last_reviewed", "unknown")

    critical_gaps: List[str] = []
    major_gaps: List[str] = []
    minor_gaps: List[str] = []

    for doc in missing:
        sev = _classify_document(str(doc))
        if sev == "CRITICAL":
            critical_gaps.append(str(doc))
        elif sev == "MAJOR":
            major_gaps.append(str(doc))
        else:
            minor_gaps.append(str(doc))

    inspection_ready = (pct >= 95) and (len(critical_gaps) == 0)

    if critical_gaps or pct < 75:
        risk = "CRITICAL"
    elif major_gaps or pct < 90:
        risk = "HIGH"
    elif pct < 95:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    findings: List[str] = []
    if critical_gaps:
        findings.append(
            f"CRITICAL TMF gaps -- {len(critical_gaps)} inspection-critical document(s) missing: "
            + "; ".join(critical_gaps[:3])
        )
    if major_gaps:
        findings.append(
            f"MAJOR TMF gaps -- {len(major_gaps)} major document(s) missing: "
            + "; ".join(major_gaps[:3])
        )
    if pct < 90:
        findings.append(f"TMF completeness {pct}% is below 90% inspection-readiness threshold")

    summary = (
        f"eTMF completeness: {pct}%. Last reviewed: {last_reviewed}. "
        f"Inspection risk: {risk}. "
        f"Gaps: {len(critical_gaps)} critical, {len(major_gaps)} major, {len(minor_gaps)} minor."
    )

    return {
        "completeness_pct": pct,
        "inspection_ready": inspection_ready,
        "critical_gaps": critical_gaps,
        "major_gaps": major_gaps,
        "minor_gaps": minor_gaps,
        "inspection_risk": risk,
        "findings": findings,
        "summary": summary,
        "last_reviewed": last_reviewed,
    }
