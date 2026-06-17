# tools/cohort_definer.py
# ============================================================
# Cohort Definer — translates a research question and parameters
# into a computable cohort definition spec.
#
# The LLM orchestrates the design intent; this module converts
# structured inputs to a deterministic, validatable cohort spec
# that can be executed by the RWD cohort query runner.
# No statistics are generated here — only the computable definition.
# ============================================================
from __future__ import annotations

from typing import Any, Dict


# Mapping common indications to ICD-10 code sets (demo-mode simplification)
_INDICATION_CODES: Dict[str, Dict[str, Any]] = {
    "type 2 diabetes": {
        "icd10": ["E11", "E11.0", "E11.9"],
        "snomed": ["44054006"],
        "description": "Type 2 diabetes mellitus (ICD-10 E11.x)",
    },
    "moderate-to-severe psoriasis": {
        "icd10": ["L40", "L40.0", "L40.8"],
        "snomed": ["9014002"],
        "description": "Psoriasis (ICD-10 L40.x)",
    },
    "treatment-resistant depression": {
        "icd10": ["F32", "F33", "F32.9"],
        "snomed": ["36923009"],
        "description": "Major depressive disorder (ICD-10 F32/F33), treatment-resistant variant",
    },
}

# Study design to follow-up/index-date defaults
_DESIGN_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "Retrospective Cohort": {
        "washout_period": "6 months",
        "index_date": "first qualifying prescription or encounter",
        "min_enrollment_days": 180,
    },
    "Comparative Cohort": {
        "washout_period": "12 months",
        "index_date": "first qualifying prescription or encounter",
        "min_enrollment_days": 365,
    },
    "Cross-sectional Cohort": {
        "washout_period": "none",
        "index_date": "study period cross-section date",
        "min_enrollment_days": 90,
    },
}


def define_cohort(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate research question fields into a computable cohort definition.

    Returns a structured dict that can be passed directly to run_cohort_query.
    All fields are deterministic — no LLM involved here.
    """
    indication = (state.get("indication") or "").lower()
    study_design = state.get("study_design_type", "Retrospective Cohort")
    time_horizon = state.get("time_horizon", "12 months")

    indication_codes = _INDICATION_CODES.get(indication, {
        "icd10": [],
        "snomed": [],
        "description": f"Custom indication: {indication}",
    })

    design_defaults = _DESIGN_DEFAULTS.get(study_design, _DESIGN_DEFAULTS["Retrospective Cohort"])

    return {
        "indication": state.get("indication", ""),
        "indication_codes": indication_codes,
        "intervention": state.get("intervention", ""),
        "comparator": state.get("comparator", ""),
        "outcome": state.get("outcome", ""),
        "time_horizon": time_horizon,
        "data_source": state.get("data_source", ""),
        "study_design": study_design,
        "washout_period": design_defaults["washout_period"],
        "index_date": design_defaults["index_date"],
        "min_enrollment_days": design_defaults["min_enrollment_days"],
        "follow_up": time_horizon,
        "age_restriction": "adults (18+ years)",
        "exclusions": [
            "missing index date",
            "enrollment gap > 45 days during follow-up",
            "prior use of intervention during washout period",
        ],
        "phi_note": "All outputs must be aggregate de-identified counts only (>= 11 per cell).",
    }


def validate_cohort_definition(cohort_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a cohort definition contains all required fields.
    Returns {valid: bool, issues: List[str]}.
    """
    required = ["indication", "intervention", "comparator", "outcome",
                "time_horizon", "data_source", "study_design"]
    issues = [f for f in required if not cohort_def.get(f)]
    return {"valid": len(issues) == 0, "issues": issues}
