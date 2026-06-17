# agent/nodes.py
# ============================================================
# Node functions for the RWE/HEOR workflow.
#
# Workflow:
#   intake -> define_cohort -> run_cohort_query -> assess_data_quality ->
#   synthesize_evidence -> grounding_check ->
#   [routing] -> human_review_gate -> finalize -> END
#
# The LLM orchestrates synthesis; validated statistical computation runs in
# cohort_query_runner. Routing disposition is set INSIDE grounding_check node
# so it persists in state. interrupt_before=["human_review_gate"] enforces HITL.
# ============================================================
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from agent.state import RecommendedAction, RWEHEORState
from tools import (
    gateway_tools,
    cohort_definer,
    cohort_query_runner,
    data_quality_assessor,
    evidence_synthesizer,
    rwe_checker,
)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _audit(state: RWEHEORState, action: str, node: str,
           sources=None, model: str = "") -> Dict[str, Any]:
    return {
        "timestamp": _now(),
        "actor": "ai_agent",
        "action": action,
        "node": node,
        "data_sources_accessed": sources or [],
        "ai_model_used": model,
        "human_review_required": node in ("synthesize_evidence", "finalize"),
    }


def _claims(state: RWEHEORState) -> Dict[str, Any]:
    return state.get("acting_user_claims") or {
        "sub": "demo-epidemiologist", "custom:hcls_role": "EPIDEMIOLOGIST",
    }


def intake(state: RWEHEORState) -> RWEHEORState:
    state["current_step"] = "intake"
    state.setdefault("revision_count", 0)
    state.setdefault("completed_steps", [])
    state.setdefault("audit_trail", [])
    state["case_status"] = "ANALYZING"
    state["audit_trail"].append(_audit(
        state,
        "Intake of RWE/HEOR research question: "
        + str(state.get("research_question", ""))[:80],
        "intake",
    ))
    state["completed_steps"].append("intake")
    return state


def define_cohort(state: RWEHEORState) -> RWEHEORState:
    """Translate research question to computable cohort definition."""
    state["current_step"] = "define_cohort"

    cohort_def = cohort_definer.define_cohort(dict(state))
    state["cohort_definition"] = cohort_def

    validation = cohort_definer.validate_cohort_definition(cohort_def)
    state["cohort_definition_valid"] = validation["valid"]
    state["cohort_definition_issues"] = validation["issues"]

    state["audit_trail"].append(
        _audit(state, "Defined computable cohort from research question", "define_cohort")
    )
    state["completed_steps"].append("define_cohort")
    return state


def run_cohort_query(state: RWEHEORState) -> RWEHEORState:
    """Execute cohort query via gateway; fall back to demo fixture."""
    state["current_step"] = "run_cohort_query"
    claims = _claims(state)
    sources = []

    try:
        raw = gateway_tools.run_cohort_query(claims, state.get("cohort_definition", {}))
        if raw:
            state["cohort_results"] = raw
            sources.append("rwd")
        else:
            raise ValueError("empty gateway result")
    except Exception as exc:
        state.setdefault("errors", []).append({
            "step": "run_cohort_query", "error": str(exc),
            "timestamp": _now(), "recoverable": True,
        })
        state["cohort_results"] = cohort_query_runner.run_demo_query(
            state.get("cohort_definition", {})
        )

    # Validated statistical compute — separate from LLM
    state["summary_statistics"] = cohort_query_runner.compute_summary_statistics(
        state["cohort_results"]
    )

    state["audit_trail"].append(
        _audit(state, "Ran de-identified cohort query (aggregate only)",
               "run_cohort_query", sources)
    )
    state["completed_steps"].append("run_cohort_query")
    return state


def assess_data_quality(state: RWEHEORState) -> RWEHEORState:
    """Assess RWD quality: completeness, cell suppression, balance, confounding."""
    state["current_step"] = "assess_data_quality"

    cohort = dict(state.get("cohort_results", {}))
    # Inject indication so confounding flags fire correctly
    cohort["indication"] = state.get("indication", "")

    qa = data_quality_assessor.assess_data_quality(cohort)
    state["data_quality"] = qa

    if qa.get("concerns"):
        state.setdefault("errors", []).extend([
            {"step": "assess_data_quality", "error": c, "timestamp": _now(), "recoverable": True}
            for c in qa["concerns"]
        ])

    state["audit_trail"].append(
        _audit(state,
               "Assessed data quality: " + data_quality_assessor.format_quality_summary(qa),
               "assess_data_quality")
    )
    state["completed_steps"].append("assess_data_quality")
    return state


def synthesize_evidence(state: RWEHEORState) -> RWEHEORState:
    """Draft evidence synthesis. LLM summarizes validated stats only."""
    state["current_step"] = "synthesize_evidence"
    out = evidence_synthesizer.draft_synthesis(dict(state))
    state["evidence_synthesis"] = out["evidence_synthesis"]
    state["drafted_by"] = out["drafted_by"]
    state["audit_trail"].append(
        _audit(state, "Drafted evidence synthesis (LLM narrative, stats pre-computed)",
               "synthesize_evidence", model=out["drafted_by"])
    )
    state["completed_steps"].append("synthesize_evidence")
    return state


def grounding_check(state: RWEHEORState) -> RWEHEORState:
    """Run grounding + quality gates; set routing disposition in state."""
    state["current_step"] = "grounding_check"
    text = state.get("evidence_synthesis", "")

    state["quality_findings"] = rwe_checker.quality_findings(text)
    state["grounding_report"] = rwe_checker.grounding_findings(text, dict(state))

    grounding = state["grounding_report"]
    findings = state["quality_findings"]
    ungrounded = (
        grounding.get("ungrounded_numbers", []) + grounding.get("ungrounded_entities", [])
    )

    # Causal/absolute language always escalates
    causal = any("causal" in f or "absolute" in f for f in findings)
    # Cell suppression escalates
    cell_suppressed = state.get("data_quality", {}).get("cell_suppression_required", False)

    if causal or cell_suppressed:
        state["recommended_action"] = RecommendedAction.ESCALATE
    elif (ungrounded or findings) and state.get("revision_count", 0) < 1:
        state["recommended_action"] = RecommendedAction.REVISE
        state["revision_count"] = state.get("revision_count", 0) + 1
    else:
        state["recommended_action"] = RecommendedAction.APPROVE_SYNTHESIS

    state["audit_trail"].append(
        _audit(state, "Ran grounding + quality checks", "grounding_check")
    )
    state["completed_steps"].append("grounding_check")
    return state


def routing_decision(state: RWEHEORState) -> str:
    """Pure read of disposition set in grounding_check (no state mutation)."""
    if state.get("recommended_action") == RecommendedAction.REVISE:
        return "synthesize_evidence"
    return "human_review_gate"


def human_review_gate(state: RWEHEORState) -> RWEHEORState:
    """HITL pause. Graph compiles with interrupt_before=['human_review_gate']."""
    state["current_step"] = "human_review_gate"
    state["case_status"] = "PENDING_REVIEW"
    state["audit_trail"].append({
        **_audit(state,
                 "Awaiting Epidemiologist review of evidence synthesis",
                 "human_review_gate"),
        "actor": "system",
        "human_review_required": True,
    })
    state["completed_steps"].append("human_review_gate")
    return state


def finalize(state: RWEHEORState) -> RWEHEORState:
    """Lock audit trail after Epidemiologist sign-off."""
    state["current_step"] = "finalize"
    state["case_status"] = "FINALIZED"
    state["audit_trail"].append({
        **_audit(state,
                 "Evidence synthesis finalized (post Epidemiologist review)",
                 "finalize", ["rwd"]),
        "human_review_required": True,
        "actor": state.get("acting_user_claims", {}).get("sub", "system"),
    })
    state["completed_steps"].append("finalize")
    return state
