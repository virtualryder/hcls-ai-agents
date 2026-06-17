"""MCP authorization gateway — reference logic for Bedrock AgentCore Gateway + Identity."""
from .audit import GatewayAuditLog  # noqa: F401
from .errors import ApprovalRequired, GatewayError, PolicyDenied  # noqa: F401
from .gateway import GatewayResult, MCPGateway  # noqa: F401
from .policy import PolicyDecision, decide  # noqa: F401

__all__ = [
    "MCPGateway", "GatewayResult", "GatewayAuditLog",
    "GatewayError", "PolicyDenied", "ApprovalRequired",
    "PolicyDecision", "decide",
]
