# tools/regulatory_intelligence.py
# ============================================================
# Regulatory intelligence — obligations + guidance retrieval.
#
# In production these resolve through the gateway (rim.get_obligations,
# rim.search_guidance) against Veeva Vault RIM / authority guidance corpora.
# The fixtures keep the demo fully offline.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List


def summarize_guidance(guidance_hits: List[Dict[str, Any]]) -> str:
    if not guidance_hits:
        return "No guidance retrieved."
    lines = [f"- {g.get('authority', '?')}: {g.get('title', '?')} ({g.get('ref', 'n/a')})"
             for g in guidance_hits]
    return "\n".join(lines)


def open_obligations(obligations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [o for o in obligations if o.get("status") == "open"]
