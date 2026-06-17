# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Quality CAPA agent.
# Agent 05 tools: qms.get_complaint, qms.search_similar,
#                 qms.create_capa_draft [HIGH-RISK], qms.close_capa [HIGH-RISK]
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "05-quality-capa"

try:
    from hcls_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
            approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. "
            "QMS access must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                           args=args, approval=approval)


def get_complaint(claims: Dict[str, Any], complaint_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "qms.get_complaint", {"complaint_id": complaint_id})
    return res.result if res.allowed else {}


def search_similar(claims: Dict[str, Any], query: Dict[str, Any]) -> List[Dict[str, Any]]:
    res = _invoke(claims, "qms.search_similar", {"query": query})
    return res.result if res.allowed else []


def create_capa_draft(claims: Dict[str, Any], payload: Dict[str, Any],
                      approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): requires Qualified Person approval."""
    return _invoke(claims, "qms.create_capa_draft", payload, approval=approval)


def close_capa(claims: Dict[str, Any], capa_id: str,
               approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write/irreversible): requires Qualified Person approval."""
    return _invoke(claims, "qms.close_capa", {"capa_id": capa_id}, approval=approval)
