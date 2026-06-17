# tools/duplicate_checker.py
# ============================================================
# Duplicate ICSR detection — demo-mode search.
#
# In production, duplicate detection routes through the MCP gateway to the
# safety database (Argus / Veeva Safety: safety.search_duplicates). In demo
# mode, a simple fixture-based heuristic checks whether the state matches any
# known case identifiers, returning a realistic empty or populated candidate list.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List

# Demo fixture: known case keys that would trigger a duplicate match
_KNOWN_CASES = [
    {
        "case_id": "ICSR-2025-00001",
        "suspect_drug": "Metformin",
        "meddra_pt": "Hepatotoxicity",
        "patient_age": "52 years",
        "reporter_name": "Dr. Smith",
        "match_score": 0.91,
    },
]


def demo_search(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Demo-mode duplicate search.
    Returns matching fixture cases only when the case_id contains 'DUPLICATE'
    (for test scenarios); otherwise returns an empty list to simulate a clean case.
    """
    case_id = state.get("case_id", "")
    if "DUPLICATE" in case_id.upper():
        return _KNOWN_CASES
    return []
