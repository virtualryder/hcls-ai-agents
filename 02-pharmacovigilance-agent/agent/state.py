# agent/state.py
# ============================================================
# PharmacovigilanceState — state object for an ICSR Case Intake workflow.
#
# Context of use (GVP, ICH E2B(R3), 21 CFR Part 11): the agent PARSES adverse-
# event source records, EXTRACTS case fields, CODES terms, ASSESSES seriousness,
# and DRAFTS an ICSR narrative for a PV Medical Reviewer. It does NOT determine
# causality, finalize a case, or submit to a regulatory authority without a
# qualified PV Medical Reviewer sign-off. Every field maps to an ICH E2B(R3)
# data element or audit requirement.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    """Disposition for a drafted ICSR case narrative."""
    APPROVE_DRAFT = "APPROVE_DRAFT"   # clean: route to PV Medical Reviewer for sign-off
    REVISE = "REVISE"                 # grounding / quality issues: send back (bounded)
    ESCALATE = "ESCALATE"            # PHI leak or fatal quality concern: senior PV review


class PharmacovigilanceState(TypedDict, total=False):
    # ── Intake / source ───────────────────────────────────────────────────────
    case_id: str
    source_type: str            # EMAIL | LITERATURE | CALL_CENTER | SPONTANEOUS
    raw_source: str             # raw inbound text / abstract / call transcript

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── Validity (4 ICSR elements) ────────────────────────────────────────────
    has_identifiable_patient: bool
    has_identifiable_reporter: bool
    has_suspect_product: bool
    has_adverse_event: bool
    is_valid_icsr: bool
    validity_notes: List[str]

    # ── Extracted E2B(R3) fields ──────────────────────────────────────────────
    patient_age: Optional[str]
    patient_sex: Optional[str]
    patient_weight_kg: Optional[str]
    patient_relevant_history: Optional[str]
    reporter_name: Optional[str]
    reporter_type: Optional[str]    # HEALTHCARE_PROFESSIONAL | CONSUMER | LITERATURE | OTHER
    reporter_country: Optional[str]
    suspect_drug: Optional[str]
    suspect_dose: Optional[str]
    suspect_route: Optional[str]
    suspect_indication: Optional[str]
    event_description: Optional[str]
    event_onset_date: Optional[str]
    event_outcome: Optional[str]    # RECOVERED | RECOVERING | NOT_RECOVERED | FATAL | UNKNOWN
    time_to_onset_days: Optional[str]
    dechallenge: Optional[str]      # POSITIVE | NEGATIVE | NOT_APPLICABLE | UNKNOWN
    rechallenge: Optional[str]      # POSITIVE | NEGATIVE | NOT_APPLICABLE | UNKNOWN

    # ── Coding (MedDRA + WHODrug) ─────────────────────────────────────────────
    meddra_pt: Optional[str]        # MedDRA Preferred Term
    meddra_pt_code: Optional[str]
    meddra_soc: Optional[str]       # System Organ Class
    whodrug_name: Optional[str]     # WHODrug preferred drug name
    whodrug_atc: Optional[str]      # ATC code

    # ── Duplicate search ──────────────────────────────────────────────────────
    duplicate_candidates: List[Dict[str, Any]]
    is_duplicate: bool

    # ── Seriousness assessment ────────────────────────────────────────────────
    is_serious: bool
    seriousness_criteria: List[str]   # death | life_threatening | hospitalization |
                                       # disability | congenital | other_medically_important
    expectedness: Optional[str]        # EXPECTED | UNEXPECTED
    reporting_clock_days: Optional[int]  # 7 (fatal/serious unexpected) or 15 (other serious)
    causality_assessment: Optional[str]  # RELATED | POSSIBLY_RELATED | UNRELATED | UNKNOWN

    # ── Narrative ─────────────────────────────────────────────────────────────
    narrative_text: str
    narrative_drafted_by: str         # bedrock | anthropic | demo-stub

    # ── Quality check ─────────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    phi_check_passed: bool
    required_elements_present: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    submission_case_id: Optional[str]
    case_status: str            # INTAKE | PENDING_REVIEW | APPROVED | SUBMITTED | PENDING
    revision_count: int
    reporting_deadline: Optional[str]

    # ── LangGraph / UI infra ──────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # ── Audit trail (21 CFR Part 11 / GVP Module VI) ─────────────────────────
    # Each entry: timestamp, actor, action, node, data_sources_accessed,
    # ai_model_used, human_review_required.
    audit_trail: List[Dict[str, Any]]
