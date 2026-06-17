"""HCLS Agent Platform — shared production primitives for all Life Sciences agents.

Modules:
    llm_factory   get_llm(role) — Anthropic (default) / Bedrock + Guardrails (in-account)
    auth          verify_jwt, require_role, record_reviewer_identity
    secrets       get_secret — Secrets Manager with env fallback
    phi           mask(text) — layered PHI/PII regex (HIPAA Safe Harbor identifiers)
    tracing       traced_node — OTel span per graph node, no-op fallback
    mcp_gateway   the governed front door to systems of record (ELN/LIMS/EDC/RIM/
                  Safety DB). Reference logic for Amazon Bedrock AgentCore Gateway +
                  AgentCore Identity.
    connectors    fixture/live connector framework for regulated systems of record

This package is the shared everything-else; per-agent durability lives in each
agent's agent/persistence.py. Designed so that a single workflow can be validated
(GxP / 21 CFR Part 11) once and reused across agents.
"""
from hcls_agent_platform.llm_factory import get_llm  # noqa: F401
from hcls_agent_platform.phi import luhn_valid, mask  # noqa: F401
from hcls_agent_platform.secrets import get_secret  # noqa: F401
from hcls_agent_platform.tracing import traced_node  # noqa: F401

__all__ = ["get_llm", "mask", "luhn_valid", "get_secret", "traced_node"]
__version__ = "0.1.0"
