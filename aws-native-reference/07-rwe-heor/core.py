"""
Deterministic core for the RWE/HEOR native rebuild.

All non-LLM logic lives here: cohort validation, grounding check, quality gate,
and routing. The LLM (strands_agent.py) only synthesizes narrative; this module
decides whether a synthesis is clean, needs revision, or must escalate.

Key domain rules:
  * numbers > 12 in the synthesis must appear in the grounding corpus (cohort_results)
  * causal language always escalates (RWE establishes association only)
  * cell suppression (N < 11) always escalates
  * data completeness < 80% triggers a quality warning
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
_CAUSAL = re.compile(
    r"\b(proves?\s+causation|causally\s+(?:linked|related)|definitively\s+demonstrates?|"
    r"100%\s+confident|guarantee[sd]?\s+(?:efficacy|benefit|outcome))\b",
    re.I,
)
_CELL_MIN = 11
_COMPLETENESS_THRESHOLD = 80


def _flatten(obj: Any) -> List[Any]:
    if isinstance(obj, dict):
        vals: List[Any] = []
        for v in obj.values():
            vals += _flatten(v)
        return vals
    if isinstance(obj, list):
        vals = []
        for v in obj:
            vals += _flatten(v)
        return vals
    return [obj]


def grounding_findings(text: str, corpus: Dict[str, Any]) -> List[str]:
    """Numbers > 12 in synthesis must appear in corpus values."""
    flat = " ".join(str(v) for v in _flatten(corpus))
    corpus_nums = set(_NUM.findall(flat))
    out: List[str] = []
    for tok in _NUM.findall(text):
        try:
            if float(tok) <= 12:
                continue
        except ValueError:
            continue
        if tok not in corpus_nums:
            out.append(f"ungrounded number: {tok}")
    return out


def compliance_findings(text: str, cohort_results: Dict[str, Any]) -> List[str]:
    """Detect causal language and cell-suppression violations."""
    out: List[str] = []
    if _CAUSAL.search(text):
        out.append("causal language detected — RWE establishes association only")
    n_int = cohort_results.get("n_intervention", 999)
    n_comp = cohort_results.get("n_comparator", 999)
    if isinstance(n_int, int) and n_int < _CELL_MIN:
        out.append(f"cell suppression required: n_intervention={n_int} < {_CELL_MIN}")
    if isinstance(n_comp, int) and n_comp < _CELL_MIN:
        out.append(f"cell suppression required: n_comparator={n_comp} < {_CELL_MIN}")
    completeness = cohort_results.get("data_completeness_pct")
    if completeness is not None and completeness < _COMPLETENESS_THRESHOLD:
        out.append(f"data completeness {completeness}% below {_COMPLETENESS_THRESHOLD}% threshold")
    return out


def route(
    cohort_results: Dict[str, Any],
    synthesis: str,
    revision_count: int,
) -> Dict[str, Any]:
    """
    Determine next step. Returns:
        {next: "Synthesize"|"HumanReviewGate", action: "REVISE"|"ESCALATE"|"APPROVE_SYNTHESIS",
         compliance: [...], grounding: [...]}
    """
    comp = compliance_findings(synthesis, cohort_results)
    grnd = grounding_findings(synthesis, cohort_results)

    # Causal language or cell suppression always escalates
    severe = any("causal" in c or "cell suppression" in c for c in comp)
    if severe:
        return {
            "next": "HumanReviewGate",
            "action": "ESCALATE",
            "compliance": comp,
            "grounding": grnd,
        }
    if (comp or grnd) and revision_count < 1:
        return {
            "next": "Synthesize",
            "action": "REVISE",
            "compliance": comp,
            "grounding": grnd,
        }
    return {
        "next": "HumanReviewGate",
        "action": "APPROVE_SYNTHESIS",
        "compliance": comp,
        "grounding": grnd,
    }
