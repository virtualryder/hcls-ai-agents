# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Medical Affairs MSL agent.
# Agent 08 tools: crm.get_hcp, dms.get_document,
#                 mlr.submit_for_review [HIGH-RISK]
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "08-medical-affairs-msl"

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
            "CRM/DMS/MLR access must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                           args=args, approval=approval)


def get_hcp(claims: Dict[str, Any], hcp_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "crm.get_hcp", {"hcp_id": hcp_id})
    return res.result if res.allowed else {}


def get_document(claims: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "dms.get_document", {"doc_id": doc_id})
    return res.result if res.allowed else {}


def submit_for_mlr_review(claims: Dict[str, Any], payload: Dict[str, Any],
                           approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): requires Medical Affairs Approver sign-off."""
    return _invoke(claims, "mlr.submit_for_review", payload, approval=approval)
