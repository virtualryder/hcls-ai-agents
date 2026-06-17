# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the RWE/HEOR agent.
# Agent 07 tool: rwd.run_cohort_query (single tool, read-only)
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "07-rwe-heor"

try:
    from hcls_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any]) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. "
            "RWD access must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args)


def run_cohort_query(claims: Dict[str, Any], query: Dict[str, Any]) -> Dict[str, Any]:
    """De-identified aggregate RWD cohort query. No PHI crosses the boundary.

    In demo/fixture mode the platform gateway returns a generic stub that does NOT
    contain n_intervention/n_comparator. We detect that and raise so the calling node
    falls back to the domain-specific demo fixture in cohort_query_runner.
    """
    # In demo extract mode, skip gateway and go straight to fixture fallback
    if os.environ.get("EXTRACT_MODE", "").lower() == "demo":
        raise RuntimeError("EXTRACT_MODE=demo — using cohort_query_runner fixture directly")

    res = _invoke(claims, "rwd.run_cohort_query", {"query": query})
    if not res.allowed:
        raise RuntimeError(f"Gateway denied rwd.run_cohort_query: {res.reason}")
    result = res.result or {}
    # Validate the response has the required fields for a real RWD result
    if "n_intervention" not in result:
        raise RuntimeError(
            "Gateway returned generic fixture stub (no n_intervention); "
            "using domain-specific demo fixture instead"
        )
    return result
