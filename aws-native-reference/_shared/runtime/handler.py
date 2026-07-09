"""
Shared AgentCore Runtime handler — the container contract for lifting any LangGraph
agent in this suite onto Amazon Bedrock AgentCore Runtime.

AgentCore Runtime expects an HTTP server on port 8080 exposing:
    POST /invocations   run the agent on a JSON payload, return JSON
    GET  /ping          health/readiness

This handler resolves the target agent's compiled LangGraph (by AGENT_MODULE env,
e.g. "agent.graph:build_regulatory_writing_graph"), invokes it, and returns the
final state. Inference is served by Bedrock (reached over PrivateLink) when LLM_PROVIDER=bedrock.

The same image works for all agents — only AGENT_MODULE and the copied agent code
differ. This is the "keep LangGraph, add AWS-native deployment" path.
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Dict

_GRAPH = None


def _load_graph():
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    spec = os.getenv("AGENT_MODULE", "agent.graph:build_graph")
    module_name, _, factory = spec.partition(":")
    module = importlib.import_module(module_name)
    builder = getattr(module, factory)
    # Build without the interrupt for the stateless runtime path; HITL for the
    # native path is enforced by Step Functions waitForTaskToken instead.
    _GRAPH = builder(use_memory=False)
    return _GRAPH


def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the agent graph on a payload and return the final state (JSON-safe)."""
    graph = _load_graph()
    result = graph.invoke(payload)
    return _jsonable(result)


def ping() -> Dict[str, str]:
    return {"status": "healthy"}


def _jsonable(obj: Any) -> Any:
    """Coerce enums and non-serializable values to JSON-safe forms."""
    import enum

    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)
