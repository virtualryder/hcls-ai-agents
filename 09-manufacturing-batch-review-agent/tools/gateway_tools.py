# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Manufacturing Batch-Review agent.
#
# Every system-of-record call (MES / electronic batch records, LIMS) goes through
# the MCP authorization gateway (reference logic for Bedrock AgentCore Gateway +
# Identity): the acting user's verified claims are authorized against a
# deny-by-default policy, high-risk writes (recording a disposition) require human
# approval, a short-lived scoped token is minted, and the attempt is audited.
#
# Falls back gracefully if platform_core is not importable (pure-local demo).
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "09-manufacturing-batch-review"

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
            "MES/LIMS must flow through the gateway (authorize -> token -> audit)."
        )
    return _GATEWAY.invoke(
        user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args, approval=approval,
    )


def get_batch_record(claims: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
    """Retrieve an electronic batch record from the MES."""
    res = _invoke(claims, "mes.get_batch_record", {"batch_id": batch_id})
    return res.result if res.allowed else {}


def get_lims_results(claims: Dict[str, Any], batch_id: str) -> List[Dict[str, Any]]:
    """Retrieve QC test results for a batch from the LIMS."""
    res = _invoke(claims, "lims.get_results", {"batch_id": batch_id})
    return res.result if res.allowed else []


def write_disposition_draft(claims: Dict[str, Any], payload: Dict[str, Any],
                            approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): persist a draft disposition / exception report to the MES."""
    return _invoke(claims, "mes.write_disposition_draft", payload, approval=approval)


def record_disposition(claims: Dict[str, Any], payload: Dict[str, Any],
                       approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write/irreversible): record the QA batch disposition (release/hold)."""
    return _invoke(claims, "mes.record_disposition", payload, approval=approval)
