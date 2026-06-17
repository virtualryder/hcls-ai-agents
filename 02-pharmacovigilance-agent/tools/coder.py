# tools/coder.py
# ============================================================
# MedDRA PT and WHODrug demo-mode coding.
#
# In production, coding routes through the MCP gateway to a licensed MedDRA
# browser and WHODrug dictionary service. In demo mode, a small fixture table
# provides realistic coded outputs so the pipeline runs without API credentials.
# ============================================================
from __future__ import annotations

import re
from typing import Dict

# MedDRA demo fixture: event keyword -> (PT, PT_code, SOC)
_MEDDRA_FIXTURE: Dict[str, tuple] = {
    "liver": ("Hepatotoxicity", "10019851", "Hepatobiliary disorders"),
    "hepat": ("Hepatotoxicity", "10019851", "Hepatobiliary disorders"),
    "rash": ("Rash", "10037844", "Skin and subcutaneous tissue disorders"),
    "nausea": ("Nausea", "10028813", "Gastrointestinal disorders"),
    "vomit": ("Vomiting", "10047700", "Gastrointestinal disorders"),
    "cardiac": ("Cardiac failure", "10007554", "Cardiac disorders"),
    "heart": ("Cardiac failure", "10007554", "Cardiac disorders"),
    "anaphyla": ("Anaphylactic reaction", "10002198", "Immune system disorders"),
    "seizure": ("Seizure", "10039906", "Nervous system disorders"),
    "stroke": ("Cerebrovascular accident", "10008190", "Nervous system disorders"),
    "bleed": ("Haemorrhage", "10018965", "Vascular disorders"),
    "thrombos": ("Deep vein thrombosis", "10051055", "Vascular disorders"),
    "pain": ("Pain", "10033371", "General disorders and administration site conditions"),
    "death": ("Death", "10011906", "General disorders and administration site conditions"),
    "died": ("Death", "10011906", "General disorders and administration site conditions"),
    "fatal": ("Death", "10011906", "General disorders and administration site conditions"),
    "hospitali": ("Hospitalisation", "10020751", "General disorders and administration site conditions"),
    "failure": ("Organ failure", "10030302", "General disorders and administration site conditions"),
}

_DEFAULT_MEDDRA = ("Adverse drug reaction", "10001718", "General disorders and administration site conditions")

# WHODrug demo fixture: drug keyword -> (preferred_name, ATC)
_WHODRUG_FIXTURE: Dict[str, tuple] = {
    "metformin": ("Metformin", "A10BA02"),
    "atorvastatin": ("Atorvastatin", "C10AA05"),
    "lisinopril": ("Lisinopril", "C09AA03"),
    "warfarin": ("Warfarin", "B01AA03"),
    "amoxicillin": ("Amoxicillin", "J01CA04"),
    "ibuprofen": ("Ibuprofen", "M01AE01"),
    "aspirin": ("Aspirin", "B01AC06"),
    "acetylsalicylic": ("Aspirin", "B01AC06"),
    "paracetamol": ("Paracetamol", "N02BE01"),
    "acetaminophen": ("Paracetamol", "N02BE01"),
    "omeprazole": ("Omeprazole", "A02BC01"),
    "simvastatin": ("Simvastatin", "C10AA01"),
    "amlodipine": ("Amlodipine", "C08CA01"),
    "carvedilol": ("Carvedilol", "C07AG02"),
    "infliximab": ("Infliximab", "L04AB02"),
    "adalimumab": ("Adalimumab", "L04AB04"),
    "rivaroxaban": ("Rivaroxaban", "B01AF01"),
    "apixaban": ("Apixaban", "B01AF02"),
    "demo": ("Demo Drug", "N07XX99"),
}

_DEFAULT_WHODRUG = ("Unspecified drug", "N07XX99")


def code_event_demo(event_term: str) -> Dict[str, str]:
    """Return MedDRA PT + code + SOC for an adverse event term (demo fixture)."""
    lower = event_term.lower()
    for kw, (pt, code, soc) in _MEDDRA_FIXTURE.items():
        if kw in lower:
            return {"pt": pt, "pt_code": code, "soc": soc}
    return {"pt": _DEFAULT_MEDDRA[0], "pt_code": _DEFAULT_MEDDRA[1], "soc": _DEFAULT_MEDDRA[2]}


def code_drug_demo(drug_name: str) -> Dict[str, str]:
    """Return WHODrug preferred name + ATC for a drug name (demo fixture)."""
    lower = drug_name.lower()
    for kw, (name, atc) in _WHODRUG_FIXTURE.items():
        if kw in lower:
            return {"name": name, "atc": atc}
    return {"name": _DEFAULT_WHODRUG[0], "atc": _DEFAULT_WHODRUG[1]}
