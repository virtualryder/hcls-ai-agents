"""
MCP authorization policy — the heart of the AgentCore Gateway decision.

It is **deny-by-default** and enforces **least privilege as an intersection**:
a tool call is permitted only if BOTH the calling agent is granted the tool AND
the acting user is entitled to it. An agent can never do more than the human on
whose behalf it acts — even if the agent's own grant list is broader.

  permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]

High-risk (write / irreversible) tools additionally require human approval before
execution. Reads do not.

In production these tables are expressed as Amazon Bedrock AgentCore Gateway
targets + AgentCore Identity scopes (or API Gateway + Lambda authorizer + STS +
Cognito + OPA/Cedar) fed by the enterprise IdP; here they are explicit Python so
the model is testable and the intersection semantics are unambiguous. Tool names
("<connector_kind>.<operation>") map 1:1 to AgentCore Gateway target names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Tuple

# ── Tool registry: tool name -> (connector_kind, method, high_risk) ───────────
# Each tool maps onto the connector framework and an AgentCore Gateway target.
# high_risk=True => write/irreversible => human-approval gate before execution.
TOOL_REGISTRY: Dict[str, Tuple[str, str, bool]] = {
    # Regulatory information management / submission systems
    "rim.get_obligations":        ("rim", "get_obligations", False),
    "rim.search_guidance":        ("rim", "search_guidance", False),
    "rim.create_submission_draft": ("rim", "create_submission_draft", True),   # write
    # Document / content management (CSR, modules, labeling)
    "dms.get_document":           ("dms", "get_document", False),
    "dms.put_draft":              ("dms", "put_draft", True),                   # write
    # Safety database (Argus / Veeva Safety) — ICSR/AE case processing
    "safety.get_case":            ("safety", "get_case", False),
    "safety.search_duplicates":   ("safety", "search_duplicates", False),
    "safety.write_case_draft":    ("safety", "write_case_draft", True),        # write
    "safety.submit_report":       ("safety", "submit_report", True),           # write/irreversible
    # Medical coding dictionaries
    "meddra.code_term":           ("meddra", "code_term", False),
    "whodrug.code_drug":          ("whodrug", "code_drug", False),
    # Clinical systems
    "edc.get_subject_data":       ("edc", "get_subject_data", False),
    "edc.create_query":           ("edc", "create_query", True),               # write
    "ctms.get_study_status":      ("ctms", "get_study_status", False),
    "etmf.get_completeness":      ("etmf", "get_completeness", False),
    # Real-world / claims / registry data (de-identified)
    "rwd.run_cohort_query":       ("rwd", "run_cohort_query", False),
    # Quality management system
    "qms.get_complaint":          ("qms", "get_complaint", False),
    "qms.search_similar":         ("qms", "search_similar", False),
    "qms.create_capa_draft":      ("qms", "create_capa_draft", True),          # write
    "qms.close_capa":             ("qms", "close_capa", True),                 # write/irreversible
    # Manufacturing execution system (electronic batch records) + LIMS
    "mes.get_batch_record":       ("mes", "get_batch_record", False),
    "mes.write_disposition_draft": ("mes", "write_disposition_draft", True),    # write
    "mes.record_disposition":     ("mes", "record_disposition", True),          # write/irreversible
    "lims.get_results":           ("lims", "get_results", False),
    # CRM / medical affairs
    "crm.get_hcp":                ("crm", "get_hcp", False),
    "mlr.submit_for_review":      ("mlr", "submit_for_review", True),          # write
}

HIGH_RISK_TOOLS: FrozenSet[str] = frozenset(t for t, (_, _, hr) in TOOL_REGISTRY.items() if hr)

# Legally / regulatorily CONSEQUENTIAL commits — the irreversible act that closes a
# regulated record (submit an ICSR, close a CAPA, release/reject a batch). These are
# DELIBERATELY ABSENT from every AGENT_TOOL_GRANTS set below: an agent can draft and
# propose, but only a bound human reviewer identity may commit. Enforced by
# platform_core/tests/test_mcp_gateway.py::test_consequential_actions_withheld_from_agents.
CONSEQUENTIAL_COMMITS: FrozenSet[str] = frozenset({
    "safety.submit_report",     # ICSR submission (Agent 02 → PV_MEDICAL_REVIEWER)
    "qms.close_capa",           # CAPA closure   (Agent 05 → QUALIFIED_PERSON)
    "mes.record_disposition",   # batch release  (Agent 09 → QA_RELEASE)
})

# ── What each AGENT is allowed to call (its job description as code) ───────────
AGENT_TOOL_GRANTS: Dict[str, FrozenSet[str]] = {
    "01-regulatory-writing": frozenset({
        "rim.get_obligations", "rim.search_guidance", "rim.create_submission_draft",
        "dms.get_document", "dms.put_draft",
    }),
    "02-pharmacovigilance": frozenset({
        "safety.get_case", "safety.search_duplicates", "safety.write_case_draft",
        "meddra.code_term", "whodrug.code_drug",
        # NOTE: no safety.submit_report — the irreversible regulatory submission is a
        # qualified-person decision, withheld from the agent and held only by a human role.
    }),
    "03-clinical-trial-ops": frozenset({
        "ctms.get_study_status", "etmf.get_completeness", "edc.get_subject_data",
        "edc.create_query",
    }),
    "04-site-patient-matching": frozenset({
        "rwd.run_cohort_query", "ctms.get_study_status",
    }),
    "05-quality-capa": frozenset({
        "qms.get_complaint", "qms.search_similar", "qms.create_capa_draft",
        # NOTE: no qms.close_capa — CAPA closure is a quality-owner decision, withheld from the agent.
    }),
    "06-protocol-design": frozenset({
        "rim.search_guidance", "rwd.run_cohort_query", "ctms.get_study_status",
    }),
    "07-rwe-heor": frozenset({
        "rwd.run_cohort_query",
    }),
    "08-medical-affairs-msl": frozenset({
        "crm.get_hcp", "dms.get_document", "mlr.submit_for_review",
    }),
    "09-manufacturing-batch-review": frozenset({
        "mes.get_batch_record", "lims.get_results", "mes.write_disposition_draft",
        # NOTE: no mes.record_disposition — batch release/reject is a QA decision, withheld from the agent.
    }),
}

# ── What each USER ROLE is entitled to (the human's real permissions) ─────────
ROLE_ENTITLEMENTS: Dict[str, FrozenSet[str]] = {
    "REGULATORY_AUTHOR": frozenset({
        "rim.get_obligations", "rim.search_guidance", "dms.get_document", "dms.put_draft",
    }),
    "REGULATORY_APPROVER": frozenset({
        "rim.get_obligations", "rim.search_guidance", "rim.create_submission_draft",
        "dms.get_document", "dms.put_draft",
    }),
    "PV_PROCESSOR": frozenset({
        "safety.get_case", "safety.search_duplicates", "safety.write_case_draft",
        "meddra.code_term", "whodrug.code_drug",
    }),
    "PV_MEDICAL_REVIEWER": frozenset({  # processor + the irreversible submit
        "safety.get_case", "safety.search_duplicates", "safety.write_case_draft",
        "safety.submit_report", "meddra.code_term", "whodrug.code_drug",
    }),
    "CLINOPS_LEAD": frozenset({
        "ctms.get_study_status", "etmf.get_completeness", "edc.get_subject_data",
        "edc.create_query",
    }),
    "QUALITY_REVIEWER": frozenset({
        "qms.get_complaint", "qms.search_similar", "qms.create_capa_draft",
    }),
    "QUALIFIED_PERSON": frozenset({  # quality reviewer + irreversible CAPA closure
        "qms.get_complaint", "qms.search_similar", "qms.create_capa_draft", "qms.close_capa",
    }),
    "EPIDEMIOLOGIST": frozenset({"rwd.run_cohort_query", "ctms.get_study_status"}),
    "MSL": frozenset({"crm.get_hcp", "dms.get_document"}),
    "MEDICAL_AFFAIRS_APPROVER": frozenset({"crm.get_hcp", "dms.get_document", "mlr.submit_for_review"}),
    "MFG_OPERATOR": frozenset({  # read batch + LIMS, draft a disposition; cannot record it
        "mes.get_batch_record", "lims.get_results", "mes.write_disposition_draft",
    }),
    "QA_RELEASE": frozenset({  # operator rights + the irreversible disposition record (release/reject)
        "mes.get_batch_record", "lims.get_results", "mes.write_disposition_draft",
        "mes.record_disposition",
    }),
}


@dataclass
class PolicyDecision:
    allowed: bool
    tool: str
    reason: str
    requires_approval: bool = False
    connector_kind: str = ""
    method: str = ""
    effective_scope: List[str] = field(default_factory=list)  # exactly this tool


def user_entitlements(roles: Iterable[str]) -> FrozenSet[str]:
    out: set = set()
    for r in roles:
        out |= ROLE_ENTITLEMENTS.get(r, frozenset())
    return frozenset(out)


def decide_human_commit(user_roles: Iterable[str], tool: str) -> PolicyDecision:
    """Authorize a CONSEQUENTIAL_COMMIT performed by a HUMAN authority.

    These irreversible commits are withheld from every agent grant (see
    CONSEQUENTIAL_COMMITS) — no agent may ever hold them. When a qualified human
    commits (carrying a valid bound approval), authorization is by the human's ROLE
    entitlement alone; there is no agent in the loop to intersect against."""
    if tool not in TOOL_REGISTRY:
        return PolicyDecision(False, tool, f"unknown tool {tool!r}")
    if tool not in CONSEQUENTIAL_COMMITS:
        return PolicyDecision(False, tool, f"{tool!r} is not a human-commit tool")
    connector_kind, method, _ = TOOL_REGISTRY[tool]
    ent = user_entitlements(user_roles)
    if tool not in ent:
        return PolicyDecision(False, tool,
                              f"approver (roles={list(user_roles)}) is not entitled to commit {tool!r}",
                              connector_kind=connector_kind, method=method)
    return PolicyDecision(True, tool, "human-authority commit (approver role + bound approval)",
                          requires_approval=True, connector_kind=connector_kind, method=method,
                          effective_scope=[tool])


def decide(agent_id: str, user_roles: Iterable[str], tool: str) -> PolicyDecision:
    """Deny-by-default authorization with least-privilege intersection."""
    if tool not in TOOL_REGISTRY:
        return PolicyDecision(False, tool, f"unknown tool {tool!r}")

    connector_kind, method, high_risk = TOOL_REGISTRY[tool]
    agent_grants = AGENT_TOOL_GRANTS.get(agent_id, frozenset())
    if tool not in agent_grants:
        return PolicyDecision(False, tool,
                              f"agent {agent_id!r} is not granted {tool!r} (agent over-reach denied)",
                              connector_kind=connector_kind, method=method)

    ent = user_entitlements(user_roles)
    if tool not in ent:
        return PolicyDecision(False, tool,
                              f"acting user (roles={list(user_roles)}) is not entitled to {tool!r} "
                              f"(an agent may never exceed the user's own permissions)",
                              connector_kind=connector_kind, method=method)

    return PolicyDecision(
        True, tool,
        "permitted by agent grant ∩ user entitlement",
        requires_approval=tool in HIGH_RISK_TOOLS,
        connector_kind=connector_kind, method=method,
        effective_scope=[tool],
    )
