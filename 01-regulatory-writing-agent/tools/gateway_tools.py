# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Regulatory Writing agent.
#
# Every system-of-record call (RIM, DMS) goes through the MCP authorization
# gateway (reference logic for Bedrock AgentCore Gateway + Identity): the acting
# user's verified claims are authorized against deny-by-default policy with
# least-privilege intersection, high-risk writes require human approval, a
# short-lived scoped token is minted, and the attempt is audited (PHI-masked).
#
# Falls back gracefully if platform_core is not importable (pure-local demo),
# so the agent still runs — but production MUST use the gateway path.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make platform_core importable when running from the agent folder.
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "01-regulatory-writing"

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
            "RIM/DMS must flow through the gateway (authorize -> token -> audit)."
        )
    res = _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                          args=args, approval=approval)
    return res


def get_obligations(claims: Dict[str, Any], product: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "rim.get_obligations", {"product": product})
    return res.result if res.allowed else []


def search_guidance(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "rim.search_guidance", {"query": query})
    return res.result if res.allowed else []


def get_document(claims: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "dms.get_document", {"doc_id": doc_id})
    return res.result if res.allowed else {}


def create_submission_draft(claims: Dict[str, Any], payload: Dict[str, Any],
                            approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): requires a verified human approval at the gateway."""
    return _invoke(claims, "rim.create_submission_draft", payload, approval=approval)
