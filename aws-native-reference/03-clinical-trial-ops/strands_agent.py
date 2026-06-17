"""
Strands/Bedrock drafting layer for the Clinical Trial Ops native rebuild.

In EXTRACT_MODE=demo, returns a deterministic briefing built from
evidence values — no Bedrock call, no API key required.
All numeric values output in the briefing are pulled from the evidence
dict so they remain grounded.
"""
from __future__ import annotations

import os
from typing import Any, Dict

DEMO = os.environ.get("EXTRACT_MODE", "").lower() == "demo"


def _demo_brief(evidence: Dict[str, Any]) -> str:
    study_id = evidence.get("study_id", "UNKNOWN")
    protocol_id = evidence.get("protocol_id", evidence.get("protocol", "UNKNOWN"))
    enrolled = int(evidence.get("enrolled", 0))
    target = int(evidence.get("target", 1))
    tmf_data = evidence.get("tmf_data", {})
    tmf_pct = int(round(float(tmf_data.get("completeness_pct", 0))))
    missing_docs = tmf_data.get("missing_documents", [])
    risk = evidence.get("risk_score", {})
    tier = risk.get("risk_tier", "UNKNOWN")
    composite = risk.get("composite_score", 0)
    tmf_risk_val = evidence.get("tmf_risk", "UNKNOWN")
    query_rate = evidence.get("query_rate", 0)

    lines = [
        f"study health briefing — {study_id}",
        "",
        f"protocol: {protocol_id}",
        f"enrollment status: {enrolled} of {target} subjects enrolled",
        f"etmf completeness: {tmf_pct}%",
        f"query rate: {query_rate} queries per subject",
        "",
        "data quality and tmf status:",
    ]
    if missing_docs:
        lines.append(f"  missing documents: {len(missing_docs)} item(s) require attention")
        for doc in missing_docs[:3]:
            lines.append(f"  - {doc}")
    else:
        lines.append("  no missing tmf documents identified")

    lines += [
        "",
        "risk assessment:",
        f"  overall risk tier: {tier.lower()} (composite score: {composite})",
        f"  tmf inspection risk: {tmf_risk_val.lower()}",
        "",
        "recommended actions:",
    ]
    recs = risk.get("recommendations", [])
    if recs:
        for r in recs:
            lines.append(f"  - {r}")
    else:
        lines.append("  - no immediate actions required; continue standard monitoring")

    lines += [
        "",
        "this briefing requires review and approval by the clinical operations lead "
        "before distribution per governance policy.",
    ]
    return "\n".join(lines)


def draft_briefing(evidence: Dict[str, Any], revision_notes: str = "") -> str:
    """Return a study health briefing string. Uses demo fallback when EXTRACT_MODE=demo."""
    if DEMO or not os.environ.get("ANTHROPIC_API_KEY"):
        return _demo_brief(evidence)
    try:
        from strands import Agent
        from strands.models import BedrockModel

        model = BedrockModel(
            model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5"),
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        agent = Agent(model=model)
        prompt = (
            f"Draft a concise clinical operations study health briefing for the following study. "
            f"Include: enrollment status, eTMF completeness, open data queries, "
            f"risk assessment, and recommended actions. "
            f"Do not invent numbers — use only what is provided.\n\n"
            f"Evidence:\n{evidence}\n\n"
        )
        if revision_notes:
            prompt += f"Revision notes from previous review:\n{revision_notes}\n\n"
        prompt += "Briefing:"
        result = agent(prompt)
        return str(result)
    except Exception:
        return _demo_brief(evidence)
