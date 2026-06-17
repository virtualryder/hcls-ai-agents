# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Pharmacovigilance ICSR Intake agent.
#
# Every system-of-record call (safety DB, MedDRA, WHODrug) goes through the
# MCP authorization gateway (reference logic for Bedrock AgentCore Gateway +
# Identity): the acting user's verified claims are authorized against a
# deny-by-default policy, high-risk writes require human approval, a short-lived
# scoped token is minted, and the attempt is audited (PHI-masked).
#
# Falls back gracefully if platform_core is not importable (pure-local demo),
# so the agent still runs — but production MUST use the gateway path.
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "02-pharmacovigilance"

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
            "safety/MedDRA/WHODrug must flow through the gateway (authorize -> token -> audit)."
        )
    res = _GATEWAY.invoke(
        user_claims=claims,
        agent_id=AGENT_ID,
        tool=tool,
        args=args,
        approval=approval,
    )
    return res


def get_case(claims: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    """Retrieve an existing ICSR case from the safety database (Argus/Veeva Safety)."""
    res = _invoke(claims, "safety.get_case", {"case_id": case_id})
    return res.result if res.allowed else {}


def search_duplicates(claims: Dict[str, Any], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search the safety database for potential duplicate ICSRs."""
    res = _invoke(claims, "safety.search_duplicates", criteria)
    return res.result if res.allowed else []


def write_case_draft(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): create/update a case draft in the safety database."""
    return _invoke(claims, "safety.write_case_draft", payload, approval=approval)


def submit_report(claims: Dict[str, Any], payload: Dict[str, Any],
                  approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write/irreversible): submit an ICSR to the safety database."""
    return _invoke(claims, "safety.submit_report", payload, approval=approval)


def code_meddra_term(claims: Dict[str, Any], event_term: str) -> Dict[str, Any]:
    """Code an adverse event term to MedDRA PT + SOC via gateway."""
    res = _invoke(claims, "meddra.code_term", {"term": event_term})
    return res.result if res.allowed else {}


def code_whodrug(claims: Dict[str, Any], drug_name: str) -> Dict[str, Any]:
    """Code a drug name to WHODrug preferred name + ATC via gateway."""
    res = _invoke(claims, "whodrug.code_drug", {"drug": drug_name})
    return res.result if res.allowed else {}
