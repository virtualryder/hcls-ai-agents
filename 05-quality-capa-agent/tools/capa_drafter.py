# tools/capa_drafter.py
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.prompts import CAPA_PLAN_PROMPT, SYSTEM_PROMPT


def _extract_rca_text(root_causes) -> List[str]:
    if not root_causes:
        return ["Root cause under investigation."]
    result = []
    for rc in root_causes:
        if isinstance(rc, dict):
            hyp = rc.get("hypothesis") or rc.get("category") or str(rc)
            result.append(hyp)
        else:
            result.append(str(rc))
    return result


def _demo_plan(state: Dict[str, Any]) -> str:
    complaint_id = state.get("complaint_id", "COMP-XXX")
    event_lower = str(state.get("event_type", "complaint")).lower()
    severity_lower = str(state.get("severity", "major")).lower()
    product = state.get("product", "Product")
    lot = state.get("lot_number", "LOT-XXX")
    site = state.get("site", "Site")
    desc = state.get("description", "Quality event.")
    rca_texts = _extract_rca_text(state.get("root_cause_hypotheses", []))
    rca_lines = "\n".join("- " + h for h in rca_texts[:3])
    n_similar = len(state.get("similar_events", []))
    trend = ("Pattern suggests a systemic issue; preventive action scope is expanded accordingly."
             if n_similar >= 2 else
             "Isolated event; root cause investigation initiated per standard procedure.")
    return (
        f"Corrective and preventive action plan for {event_lower} {complaint_id} "
        f"(severity: {severity_lower}, product: {product}, lot: {lot}, site: {site}).\n\n"
        f"Event description: {desc}\n\n"
        f"Trend review: {n_similar} similar event(s) identified in the quality management system. {trend}\n\n"
        f"Root cause hypotheses under investigation:\n{rca_lines}\n\n"
        "Corrective actions:\n"
        "1. Immediate containment: quarantine affected lot(s) pending investigation. Due: immediately.\n"
        "2. Root cause investigation: complete five-why or fishbone analysis. "
        "Owner: quality assurance manager. Due: 15 business days.\n"
        "3. Targeted correction based on confirmed root cause. "
        "Owner: process owner. Due: 30 business days.\n\n"
        "Preventive actions:\n"
        "1. Update relevant standard operating procedures to incorporate lessons learned.\n"
        "2. Retrain affected personnel. Owner: training manager. Due: 30 business days.\n"
        "3. Implement enhanced monitoring for similar processes.\n\n"
        "Effectiveness monitoring: track recurrence rate over 90 days; target: zero repeat events.\n\n"
        "Regulatory assessment: qualified person to evaluate whether event meets applicable "
        "reporting thresholds under current regulatory requirements.\n\n"
        "This draft plan requires qualified person review and approval before implementation."
    )


def draft_capa(state: Dict[str, Any]) -> Dict[str, str]:
    demo = (os.getenv("EXTRACT_MODE", "").strip().lower() == "demo"
            or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_PROVIDER", "").lower() == "bedrock"))
    if demo:
        return {"capa_plan": _demo_plan(state), "drafted_by": "demo-stub"}
    try:
        from hcls_agent_platform import get_llm
        rca_texts = _extract_rca_text(state.get("root_cause_hypotheses", []))
        prompt = CAPA_PLAN_PROMPT.format(
            complaint_id=state.get("complaint_id", ""),
            event_type=state.get("event_type", ""),
            severity=state.get("severity", ""),
            product=state.get("product", ""),
            lot_number=state.get("lot_number", ""),
            site=state.get("site", ""),
            description=state.get("description", ""),
            similar_events=str(state.get("similar_events", [])),
            root_causes="\n".join(rca_texts),
        )
        llm = get_llm("narrative")
        resp = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
        text = getattr(resp, "content", None) or str(resp)
        return {"capa_plan": str(text), "drafted_by": os.getenv("LLM_PROVIDER", "anthropic")}
    except Exception:
        return {"capa_plan": _demo_plan(state), "drafted_by": "demo-stub-fallback"}
