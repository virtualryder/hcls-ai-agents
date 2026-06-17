"""Reference Agent-to-Agent (A2A) pattern — governed through the MCP gateway.

A2A is NOT used by the current eight-agent suite (each agent is an independent,
in-process LangGraph). This package is the worked reference for *when* multi-agent
is needed: a supervisor invoking a specialist over a governed, identity-propagating,
audited hop. See ENTERPRISE-PLATFORM.md ADR-001 and a2a/README.md.
"""
from .supervisor import A2ARequest, A2AResult, A2ASupervisor  # noqa: F401

__all__ = ["A2ASupervisor", "A2ARequest", "A2AResult"]
