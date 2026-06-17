# tools/data_quality_assessor.py
# ============================================================
# Data Quality Assessor — evaluates RWD cohort quality before synthesis.
#
# Runs deterministic quality checks on cohort results:
#   * data completeness (threshold >= 80%)
#   * cell suppression (minimum N >= 11 per de-identification rules)
#   * balance check (intervention and comparator cohorts within 3x)
#   * confounding risk flags
#
# These checks inform the Epidemiologist and grounding report.
# No LLM involvement — pure deterministic logic.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List, Tuple


_COMPLETENESS_THRESHOLD = 80      # percent; below this = quality concern
_BALANCE_RATIO_MAX = 3.0          # n_larger / n_smaller; above = imbalance flag
_CELL_MIN = 11                    # minimum cell count for de-identified reporting


def assess_data_quality(cohort_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all data quality checks on cohort_results.

    Returns:
        {
            "quality_score": int (0-100),
            "concerns": List[str],
            "warnings": List[str],
            "data_completeness_pct": Optional[int],
            "cell_suppression_required": bool,
            "cohort_balance": str,  # "BALANCED" | "IMBALANCED"
            "confounding_flags": List[str],
        }
    """
    concerns: List[str] = []
    warnings: List[str] = []
    deductions = 0

    # 1. Data completeness
    completeness = cohort_results.get("data_completeness_pct")
    cell_suppression = False
    if completeness is not None:
        if completeness < _COMPLETENESS_THRESHOLD:
            concerns.append(
                f"data completeness {completeness}% is below {_COMPLETENESS_THRESHOLD}% threshold — "
                "interpret results with caution"
            )
            deductions += 20
        missing_note = cohort_results.get("missing_data_note", "")
        if missing_note:
            warnings.append(f"missing data: {missing_note}")

    # 2. Cell suppression check
    n_int = cohort_results.get("n_intervention", 0) or 0
    n_comp = cohort_results.get("n_comparator", 0) or 0
    if isinstance(n_int, int) and n_int < _CELL_MIN:
        concerns.append(
            f"intervention cohort N={n_int} is below minimum reporting threshold ({_CELL_MIN}); "
            "results must be suppressed per de-identification rules"
        )
        cell_suppression = True
        deductions += 30
    if isinstance(n_comp, int) and n_comp < _CELL_MIN:
        concerns.append(
            f"comparator cohort N={n_comp} is below minimum reporting threshold ({_CELL_MIN}); "
            "results must be suppressed"
        )
        cell_suppression = True
        deductions += 30

    # 3. Cohort balance
    balance = "BALANCED"
    if isinstance(n_int, int) and isinstance(n_comp, int) and n_int > 0 and n_comp > 0:
        ratio = max(n_int, n_comp) / min(n_int, n_comp)
        if ratio > _BALANCE_RATIO_MAX:
            balance = "IMBALANCED"
            warnings.append(
                f"cohort size ratio is {ratio:.1f}x — consider propensity score matching or weighting"
            )
            deductions += 10

    # 4. Confounding risk flags
    confounding_flags: List[str] = []
    indication = cohort_results.get("indication", "")
    if "diabetes" in str(indication).lower() or "cardiovascular" in str(indication).lower():
        confounding_flags.append(
            "metabolic confounders likely (BMI, prior CV events) — PS adjustment recommended"
        )
    if "psoriasis" in str(indication).lower() or "biologic" in str(indication).lower():
        confounding_flags.append(
            "channeling bias risk: biologic-naive vs biologic-experienced populations may differ"
        )
    if "depression" in str(indication).lower():
        confounding_flags.append(
            "severity confounding: treatment-resistant patients likely have higher baseline burden"
        )

    quality_score = max(0, 100 - deductions)

    return {
        "quality_score": quality_score,
        "concerns": concerns,
        "warnings": warnings,
        "data_completeness_pct": completeness,
        "cell_suppression_required": cell_suppression,
        "cohort_balance": balance,
        "confounding_flags": confounding_flags,
    }


def format_quality_summary(qa: Dict[str, Any]) -> str:
    """Return a human-readable one-line quality summary."""
    score = qa.get("quality_score", 0)
    n_concerns = len(qa.get("concerns", []))
    label = "HIGH" if score >= 80 else ("MODERATE" if score >= 60 else "LOW")
    return (
        f"data quality: {label} (score {score}/100, {n_concerns} concern(s), "
        f"balance: {qa.get('cohort_balance', 'unknown')})"
    )
