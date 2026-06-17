# tools/site_ranker.py
# ============================================================
# Site ranking drafter — LLM DRAFTING layer for site feasibility.
# Demo fallback requires no API key.
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prompts import SITE_RANKING_PROMPT, SYSTEM_PROMPT


def _demo_report(state: Dict[str, Any]) -> str:
    study_id = state.get("study_id", "STUDY-XXX")
    indication = state.get("indication", "the indication")
    target = state.get("target_enrollment", "N/A")
    cohort = state.get("cohort_results", {})
    total_eligible = cohort.get("total_eligible", 0)
    rankings = state.get("site_rankings", [])
    flags = state.get("fairness_flags", [])

    n_flags = len(flags)
    top_sites = rankings[:3]
    top_names = ", ".join(s.get("site_id", "N/A") for s in top_sites) if top_sites else "N/A"

    report = (
        f"Site feasibility and patient matching report for {study_id} ({indication}). "
        f"Target enrollment: {target} subjects. "
        f"Cohort query identified {total_eligible} potentially eligible patients "
        f"across {cohort.get('sites_with_data', len(rankings))} sites "
        f"(aggregate counts; all patient data is de-identified at source). "
        f"Top sites by eligible pool: {top_names}. "
    )
    if flags:
        flag_descs = "; ".join(f.get("description", str(f)) for f in flags[:2])
        report += f"Fairness review identified {n_flags} demographic concern(s): {flag_descs}. "
    report += (
        "Note: all patient data is aggregate and de-identified; PHI remains at source systems. "
        "Recommended actions: activate top-ranked sites and implement targeted outreach to "
        "address under-represented demographic groups. "
        "This report requires human review and approval before any site outreach begins."
    )
    return report


def draft_report(state: Dict[str, Any]) -> Dict[str, str]:
    """Return {ranking_report, drafted_by}. Demo fallback requires no API key."""
    demo = (
        os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
        or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock")
    )
    if demo:
        return {"ranking_report": _demo_report(state), "drafted_by": "demo-stub"}

    try:
        from hcls_agent_platform import get_llm

        prompt = SITE_RANKING_PROMPT.format(
            study_id=state.get("study_id", ""),
            protocol_id=state.get("protocol_id", ""),
            indication=state.get("indication", ""),
            target_enrollment=state.get("target_enrollment", ""),
            eligibility_criteria=str(state.get("eligibility_criteria", {})),
            cohort_results=str(state.get("cohort_results", {})),
            site_statuses=str(state.get("site_statuses", [])),
            fairness_flags=str(state.get("fairness_flags", [])),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        return {"ranking_report": str(text), "drafted_by": provider}
    except Exception:
        return {"ranking_report": _demo_report(state), "drafted_by": "demo-stub-fallback"}
