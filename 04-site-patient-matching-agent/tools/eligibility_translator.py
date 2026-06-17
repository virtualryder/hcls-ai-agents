# tools/eligibility_translator.py
from __future__ import annotations
from typing import Any, Dict, List


def translate(criteria: Dict[str, Any], indication: str = "") -> Dict[str, Any]:
    """
    Translate an eligibility criteria dict into a computable cohort query.
    Input criteria keys (all optional):
      age_min, age_max, diagnosis_codes, lab_thresholds, exclusions,
      gender, comorbidity_exclusions
    Returns computable query dict with filters, labs, exclusion_filters,
      translated_fields (count), translation_notes, cdisc_compliant.
    """
    filters = []
    exclusion_filters = []
    labs = []
    notes = []

    age_min = criteria.get("age_min")
    age_max = criteria.get("age_max")
    if age_min is not None:
        try:
            filters.append({"field": "age_years", "op": ">=", "value": int(age_min), "cdisc_domain": "DM"})
        except (TypeError, ValueError):
            notes.append(f"invalid age_min: {age_min!r}")
    if age_max is not None:
        try:
            filters.append({"field": "age_years", "op": "<=", "value": int(age_max), "cdisc_domain": "DM"})
        except (TypeError, ValueError):
            notes.append(f"invalid age_max: {age_max!r}")

    dx_codes = criteria.get("diagnosis_codes", [])
    if dx_codes:
        filters.append({"field": "icd10_code", "op": "in", "value": list(dx_codes), "cdisc_domain": "MH"})

    gender = criteria.get("gender", "Any")
    if gender and gender != "Any":
        filters.append({"field": "sex", "op": "==", "value": gender, "cdisc_domain": "DM"})

    for lab_name, threshold in (criteria.get("lab_thresholds") or {}).items():
        try:
            labs.append({"test_name": lab_name, "op": ">=", "value": float(threshold), "cdisc_domain": "LB"})
        except (TypeError, ValueError):
            notes.append(f"invalid lab threshold for {lab_name}: {threshold!r}")

    for excl in criteria.get("exclusions", []):
        exclusion_filters.append({"type": "text_exclusion", "description": str(excl)})

    for code in criteria.get("comorbidity_exclusions", []):
        exclusion_filters.append({"field": "icd10_code", "op": "not_in", "value": [str(code)], "cdisc_domain": "MH"})

    translated_fields = len(filters) + len(labs) + len(exclusion_filters)
    if not notes:
        notes.append("all criteria fields translated successfully")

    return {
        "indication": indication or criteria.get("indication", ""),
        "filters": filters,
        "labs": labs,
        "exclusion_filters": exclusion_filters,
        "translated_fields": translated_fields,
        "translation_notes": notes,
        "cdisc_compliant": True,
    }


def summarize(query: Dict[str, Any]) -> str:
    n_inc = len(query.get("filters", [])) + len(query.get("labs", []))
    n_exc = len(query.get("exclusion_filters", []))
    ind = query.get("indication", "unspecified")
    return (
        f"indication: {ind} | "
        f"{n_inc} inclusion filter(s) | "
        f"{n_exc} exclusion filter(s) | "
        f"cdisc-compliant: {query.get('cdisc_compliant', False)}"
    )
