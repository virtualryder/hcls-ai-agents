# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Clinical Trial Ops agent.
# Agent 03 tools: ctms.get_study_status, etmf.get_completeness,
#                 edc.get_subject_data, edc.create_query [HIGH-RISK]
# Falls back gracefully if platform_core is not importable (pure-local demo).
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "03-clinical-trial-ops"

try:
    from hcls_agent_platform.mcp_gateway import MCPGateway

    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover - standalone demo without platform_core
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
            approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. Production access to "
            "CTMS/eTMF/EDC must flow through the gateway."
        )
    res = _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                          args=args, approval=approval)
    return res


def get_study_status(claims: Dict[str, Any], study_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "ctms.get_study_status", {"study_id": study_id})
    return res.result if res.allowed else {}


def get_tmf_completeness(claims: Dict[str, Any], study_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "etmf.get_completeness", {"study_id": study_id})
    return res.result if res.allowed else {}


def get_subject_data(claims: Dict[str, Any], study_id: str,
                     site_id: Optional[str] = None) -> List[Dict[str, Any]]:
    args: Dict[str, Any] = {"study_id": study_id}
    if site_id:
        args["site_id"] = site_id
    res = _invoke(claims, "edc.get_subject_data", args)
    return res.result if res.allowed else []


def create_edc_query(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): requires a verified human approval at the gateway."""
    return _invoke(claims, "edc.create_query", payload, approval=approval)
