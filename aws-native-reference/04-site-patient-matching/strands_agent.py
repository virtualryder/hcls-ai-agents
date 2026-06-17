"""Strands/Bedrock drafting layer for the Site Patient Matching native rebuild."""
from __future__ import annotations

import os
from typing import Any, Dict

DEMO = os.environ.get("EXTRACT_MODE", "").lower() == "demo"


def _demo_report(evidence: Dict[str, Any]) -> str:
    study_id = evidence.get("study_id", "UNKNOWN")
    indication = evidence.get("indication", "the indication")
    target = int(evidence.get("target_enrollment", 0))
    cohort = evidence.get("cohort_results", {})
    total_eligible = int(cohort.get("total_eligible", 0))
    n_sites = len(cohort.get("site_counts", []))
    flags = evidence.get("fairness_flags", [])
    n_flags = len(flags)

    lines = [
        f"site feasibility and patient matching report --- {study_id}",
        "",
        f"indication: {indication}",
        f"target enrollment: {target} subjects",
        f"cohort query identified {total_eligible} potentially eligible patients"
        f" across {n_sites} sites",
        "(aggregate counts; all patient data is de-identified at source per 45 CFR 164.514)",
        "",
        "site ranking by eligible patient pool:",
    ]
    for s in sorted(cohort.get("site_counts", []),
                    key=lambda x: x.get("eligible_count", 0), reverse=True)[:3]:
        lines.append(f"  - {s.get('site_id', 'UNKNOWN')}: {s.get('eligible_count', 0)} eligible")

    if flags:
        lines.append("")
        lines.append(f"equity review: {n_flags} demographic flag(s) identified")
        for f in flags[:2]:
            lines.append(
                f"  - {f.get('site_id', '')}: {f.get('demographic', '')} "
                f"({f.get('site_pct', 0)}% vs benchmark {f.get('benchmark_pct', 0)}%)"
            )

    lines += [
        "",
        "recommended action: review and approve ranked site list before initiating outreach.",
        "this report requires human approval by the site selection lead.",
    ]
    return "\n".join(lines)


def draft_report(evidence: Dict[str, Any], revision_notes: str = "") -> str:
    if DEMO or not os.environ.get("ANTHROPIC_API_KEY"):
        return _demo_report(evidence)
    try:
        from strands import Agent
        from strands.models import BedrockModel

        model = BedrockModel(
            model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5"),
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        agent = Agent(model=model)
        prompt = (
            f"Draft a concise clinical trial site feasibility and patient matching report. "
            f"PHI note: all patient data is aggregate and de-identified. "
            f"Include: eligible patient pool size, site ranking, demographic representativeness, "
            f"recommended site activation priorities. Do not invent numbers.\n\n"
            f"Evidence:\n{evidence}\n"
        )
        if revision_notes:
            prompt += f"\nRevision notes:\n{revision_notes}\n"
        result = agent(prompt + "\nReport:")
        return str(result)
    except Exception:
        return _demo_report(evidence)
