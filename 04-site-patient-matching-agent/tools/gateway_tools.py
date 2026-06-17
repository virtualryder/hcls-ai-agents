# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Site Patient Matching agent.
# Agent 04 tools: rwd.run_cohort_query, ctms.get_study_status (read-only)
# PHI stays at source; only aggregate counts returned.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "04-site-patient-matching"

try:
    from hcls_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any]) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. "
            "RWD/CTMS access must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args)


def run_cohort_query(claims: Dict[str, Any], query: Dict[str, Any]) -> Dict[str, Any]:
    """De-identified aggregate cohort counts — no PHI crosses the boundary."""
    res = _invoke(claims, "rwd.run_cohort_query", {"query": query})
    return res.result if res.allowed else {}


def get_study_status(claims: Dict[str, Any], study_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "ctms.get_study_status", {"study_id": study_id})
    return res.result if res.allowed else {}
