# tools/hcp_profiler.py
# ============================================================
# HCP Profiler — enriches and validates the HCP profile
# retrieved from the CRM (crm.get_hcp gateway tool).
#
# Deterministic logic: validates completeness, classifies engagement
# tier, identifies clinical interests relevant to the meeting topic,
# and surfaces any interaction history flags. No LLM involvement.
# ============================================================
from __future__ import annotations

from typing import Any, Dict, List


_TIER_KEYWORDS = {
    "National KOL": ["national", "kol", "thought leader", "key opinion"],
    "Regional Thought Leader": ["regional", "tier 1", "advisory board"],
    "Specialist": ["specialist", "academic", "university", "hospital"],
    "Community": [],
}


def classify_tier(hcp_profile: Dict[str, Any]) -> str:
    """Classify HCP engagement tier from profile data."""
    tier = hcp_profile.get("tier", "")
    if tier:
        return tier
    institution = str(hcp_profile.get("institution", "")).lower()
    pubs = hcp_profile.get("recent_publications", [])
    history = hcp_profile.get("meeting_history", [])

    if len(history) >= 3 and len(pubs) >= 2:
        return "National KOL"
    if "university" in institution or "academic" in institution:
        return "Specialist"
    if len(history) >= 1:
        return "Regional Thought Leader"
    return "Community"


def extract_relevant_interests(
    hcp_profile: Dict[str, Any], topic: str
) -> List[str]:
    """Return HCP clinical interests relevant to the meeting topic."""
    interests = hcp_profile.get("clinical_interests", [])
    topic_lower = topic.lower()
    relevant = [i for i in interests if any(
        kw in topic_lower or kw in i.lower()
        for kw in ["diabetes", "renal", "cardiovascular", "metabolic",
                   "psoriasis", "oncology", "cardio", "heart", "kidney"]
    )]
    return relevant if relevant else interests[:3]


def validate_hcp_profile(hcp_profile: Any) -> Dict[str, Any]:
    """
    Validate HCP profile completeness.
    Returns {valid: bool, issues: List[str], warnings: List[str]}.
    """
    if not isinstance(hcp_profile, dict):
        return {"valid": False, "issues": ["hcp_profile is not a dict"], "warnings": []}

    issues: List[str] = []
    warnings: List[str] = []

    name = hcp_profile.get("name", "")
    if not name or name.startswith("["):
        issues.append("hcp_profile.name is missing or a placeholder")
    if not hcp_profile.get("specialty"):
        warnings.append("hcp_profile.specialty is missing — brief may lack personalization")
    if not hcp_profile.get("institution"):
        warnings.append("hcp_profile.institution is missing")
    if not hcp_profile.get("clinical_interests"):
        warnings.append("hcp_profile.clinical_interests is missing — using topic defaults")

    return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}


def enrich_hcp_profile(hcp_profile: Dict[str, Any], topic: str) -> Dict[str, Any]:
    """
    Return an enriched copy of the HCP profile with derived fields added.
    Original profile is not mutated.
    """
    enriched = dict(hcp_profile)
    enriched["engagement_tier"] = classify_tier(hcp_profile)
    enriched["relevant_interests"] = extract_relevant_interests(hcp_profile, topic)
    history = hcp_profile.get("meeting_history", [])
    enriched["prior_interaction_count"] = len(history)
    enriched["last_interaction"] = history[-1] if history else None
    return enriched
