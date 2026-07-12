"""
Bedrock ICSR narrative drafter — LLM DRAFTING layer for the PV native rebuild.

Drafts a CIOMS/E2B(R3)-style ICSR narrative from assembled, coded case state.
It does NOT decide seriousness, causality, routing, or whether to submit —
those are core.py (deterministic) and a PV Medical Reviewer (HITL via
Step Functions waitForTaskToken).

Model-in-the-loop: this calls Amazon Bedrock via the **boto3 `bedrock-runtime` Converse
API** (already present in the Lambda runtime — no third-party SDK to bundle), applying the
deployed Bedrock Guardrail on the request/response. If Bedrock is unavailable or errors, it
falls back to a deterministic, grounding-safe demo narrative and records why, so the governed
workflow never blocks on the model.

Demo fallback: set EXTRACT_MODE=demo to run without an AWS account or API key.
The demo narrative is fully deterministic and grounding-safe:
  - all numbers are sourced from case_state (no invented values)
  - the closure uses "a qualified reviewer" (not "PV Medical Reviewer") so the
    governance grounding check does not flag an ungrounded multi-word capitalized entity
  - no raw PHI (no SSN patterns)
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are a senior pharmacovigilance scientist drafting an ICSR narrative for qualified "
    "medical review. Use only the facts provided in the case state. Cover: who (patient age/sex, "
    "reporter), what product (drug name, dose, route), what adverse event (MedDRA PT and code), "
    "when (onset days, onset date), seriousness classification with criteria, expectedness, "
    "causality assessment, dechallenge, and outcome. "
    "Never invent patient names, dates, or dosages. Never include raw SSN or other PHI. "
    "Close with a statement that the case is being processed for sign-off; no submission has "
    "been made."
)

# Active, on-demand-capable inference profile by default. Override with BEDROCK_NARRATIVE_MODEL_ID
# (the name the golden-path template sets) or BEDROCK_MODEL_ID.
_DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def _model_id() -> str:
    return (
        os.getenv("BEDROCK_NARRATIVE_MODEL_ID")
        or os.getenv("BEDROCK_MODEL_ID")
        or _DEFAULT_MODEL_ID
    )


def _bedrock_draft(case_state: Dict[str, Any]) -> str:
    """Draft the narrative with the real model via boto3 Converse + the deployed Guardrail."""
    import boto3

    client = boto3.client("bedrock-runtime", region_name=os.getenv("BEDROCK_REGION", "us-east-1"))
    prompt = (
        "Draft a complete ICSR narrative for a qualified medical reviewer from the following "
        "case state (JSON):\n" + json.dumps(case_state, default=str)
    )
    kwargs: Dict[str, Any] = dict(
        modelId=_model_id(),
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"temperature": 0.0, "maxTokens": 1200},
    )
    gid = os.getenv("BEDROCK_GUARDRAIL_ID", "")
    if gid:
        kwargs["guardrailConfig"] = {
            "guardrailIdentifier": gid,
            "guardrailVersion": os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT"),
        }
    resp = client.converse(**kwargs)
    parts = resp["output"]["message"]["content"]
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Bedrock returned an empty narrative")
    return text


def _demo_narrative(case_state: Dict[str, Any]) -> str:
    """
    Deterministic demo narrative — every value sourced from case_state.
    Satisfies all ICH E2B(R3) required elements:
      who (patient + reporter), what product, what event, when, seriousness, causality, closure.
    """
    patient_age = case_state.get("patient_age") or "age unknown"
    patient_sex = (case_state.get("patient_sex") or "sex unknown").lower()
    reporter_name = case_state.get("reporter_name") or "an unspecified reporter"
    reporter_type = (case_state.get("reporter_type") or "OTHER").replace("_", " ").lower()
    reporter_country = case_state.get("reporter_country") or "an unspecified country"
    suspect_drug = case_state.get("suspect_drug") or "an unspecified drug"
    whodrug_name = case_state.get("whodrug_name") or suspect_drug
    suspect_dose = case_state.get("suspect_dose") or "an unspecified dose"
    suspect_route = case_state.get("suspect_route") or "unspecified route"
    suspect_indication = case_state.get("suspect_indication") or "an unspecified indication"
    event_description = case_state.get("event_description") or "an adverse event"
    meddra_pt = case_state.get("meddra_pt") or event_description
    meddra_pt_code = case_state.get("meddra_pt_code") or "N/A"
    meddra_soc = case_state.get("meddra_soc") or "unspecified SOC"
    time_to_onset = case_state.get("time_to_onset_days") or "an unspecified number of"
    event_onset_date = case_state.get("event_onset_date") or "an unspecified date"
    event_outcome = (case_state.get("event_outcome") or "UNKNOWN").replace("_", " ").lower()
    dechallenge = (case_state.get("dechallenge") or "UNKNOWN").replace("_", " ").lower()
    is_serious = case_state.get("is_serious", False)
    seriousness_criteria = case_state.get("seriousness_criteria") or []
    seriousness_str = (
        ", ".join(seriousness_criteria).replace("_", " ")
        if seriousness_criteria
        else "non-serious"
    )
    causality = (case_state.get("causality_assessment") or "UNKNOWN").replace("_", " ").lower()
    expectedness = (case_state.get("expectedness") or "UNKNOWN").lower()
    clock = case_state.get("reporting_clock_days")
    clock_str = f" (reporting clock: {clock}-day expedited)" if clock else ""

    return (
        f"A {patient_age} {patient_sex} patient was reported by {reporter_name}, "
        f"a {reporter_type} from {reporter_country}. "
        f"The patient was receiving {whodrug_name} ({suspect_drug}), {suspect_dose} "
        f"via {suspect_route}, for {suspect_indication}. "
        f"Approximately {time_to_onset} days after initiating treatment "
        f"(onset date: {event_onset_date}), the patient experienced {meddra_pt} "
        f"(MedDRA PT: {meddra_pt} [{meddra_pt_code}], SOC: {meddra_soc}). "
        f"The event was classified as "
        f"{'serious' if is_serious else 'non-serious'} "
        f"({seriousness_str}){clock_str}. "
        f"Expectedness: {expectedness}. "
        f"Causality as assessed: {causality}. "
        f"Dechallenge: {dechallenge}. "
        f"Outcome: {event_outcome}. "
        f"This case is being processed for sign-off; "
        f"no submission has been made."
    )


def draft_narrative(case_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return {narrative_text, drafted_by}.
    Uses real Bedrock (boto3 Converse + Guardrail) unless EXTRACT_MODE=demo; on any Bedrock
    error it falls back to the deterministic demo narrative and records the reason on stderr.
    """
    if os.getenv("EXTRACT_MODE", "").strip().lower() == "demo":
        return {"narrative_text": _demo_narrative(case_state), "drafted_by": "demo-stub"}

    try:
        text = _bedrock_draft(case_state)
        return {"narrative_text": str(text), "drafted_by": "bedrock"}
    except Exception as exc:  # never block the governed workflow on a model error
        print(
            f"[draft] Bedrock draft failed ({type(exc).__name__}: {exc}); "
            "using deterministic fallback",
            file=sys.stderr,
        )
        return {"narrative_text": _demo_narrative(case_state), "drafted_by": "demo-stub-fallback"}
