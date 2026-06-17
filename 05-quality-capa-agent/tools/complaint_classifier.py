# tools/complaint_classifier.py
from __future__ import annotations
import re
from typing import Any, Dict, List

_CRITICAL_KW = re.compile(
    r"\b(death|fatal|life[- ]threatening|serious[- ]injury|recall|patient[- ]harm|"
    r"sterility|sterility[- ]failure|sterility[- ]oos|microbial[- ]growth|microbial|"
    r"contamination[- ]patient|class[- ]i)\b", re.I)
_MAJOR_KW = re.compile(
    r"\b(particulate|particle|contamination|oos|out[- ]of[- ]specification|"
    r"temperature[- ]excursion|mislabel|underfill|overfill|equipment[- ]failure|"
    r"deviation|audit[- ]finding)\b", re.I)
_REGULATORY_KW = re.compile(
    r"\b(patient|clinical|adverse|serious|fatality|hospitali[sz]|injury|"
    r"sterility|sterility[- ]failure|microbial|microbial[- ]growth|reporting[- ]obligation|"
    r"21\s+CFR|MDR|field[- ]alert|medical[- ]device[- ]report)\b", re.I)
_EVENT_MAP = {
    "STERILITY_FAILURE": re.compile(r"\b(sterility|sterility[- ]failure|sterility[- ]oos|microbial)\b", re.I),
    "OOS": re.compile(r"\b(oos|out[- ]of[- ]spec|specification[- ]failure|release[- ]failure)\b", re.I),
    "DEVIATION": re.compile(r"\b(deviation|departure|non[- ]conform|sop[- ]breach|procedure[- ]not)\b", re.I),
    "AUDIT_FINDING": re.compile(r"\b(audit|inspection|finding|fda|ema|observation)\b", re.I),
    "COMPLAINT": re.compile(r"\b(complaint|customer|consumer|report|feedback|field[- ]alert)\b", re.I),
}


def classify(description: str, declared_severity: str = "", declared_type: str = "") -> Dict[str, Any]:
    desc = description or ""
    if declared_type and declared_type not in ("", "COMPLAINT"):
        inferred_type = declared_type.lower()
    else:
        inferred_type = "complaint"
        for etype, pat in _EVENT_MAP.items():
            if pat.search(desc):
                inferred_type = etype.lower()
                break
    if declared_severity and declared_severity in ("CRITICAL", "MAJOR", "MINOR"):
        severity = declared_severity
    elif _CRITICAL_KW.search(desc):
        severity = "CRITICAL"
    elif _MAJOR_KW.search(desc):
        severity = "MAJOR"
    else:
        severity = "MINOR"
    risk_level = {"CRITICAL": "HIGH", "MAJOR": "MEDIUM", "MINOR": "LOW"}.get(severity, "LOW")
    if severity == "CRITICAL":
        reg_required = True
    elif severity == "MAJOR" and _REGULATORY_KW.search(desc):
        reg_required = True
    else:
        reg_required = False
    basis = (
        "21 CFR 314.81 (field alert) / MDR 803 (device) / ICH Q10 reporting obligations"
        if reg_required else "No mandatory reporting threshold met"
    )
    return {
        "event_type": inferred_type,
        "severity": severity,
        "risk_level": risk_level,
        "regulatory_reporting_required": reg_required,
        "reporting_obligation_basis": basis,
        "classification_method": "rules-based keyword scanning (demo mode)",
    }


def classify_batch(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"complaint_id": e.get("complaint_id", ""),
         "classification": classify(e.get("description",""), e.get("severity",""), e.get("event_type",""))}
        for e in events
    ]
