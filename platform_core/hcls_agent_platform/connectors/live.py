"""
Live connectors -- production adapters to real systems of record.

Activated by CONNECTOR_MODE=live. Credentials resolve via hcls_agent_platform
secrets.get_secret (Secrets Manager with env-var fallback).

LiveSafetyConnector: real HTTP adapter for kind='safety'. Calls a REST API at
SAFETY_BASE_URL (env). Auth via Bearer token from secret 'safety_api_token'.
Preserves exact method signatures of FixtureSafety so agent code is unchanged.

MedDRA and WHODrug remain fixture-backed in this demo (licensed API required).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import request as _urllib_request
from urllib.error import URLError

from .base import GenericConnector, SafetyConnector


# ---------------------------------------------------------------------------
# Generic live stub (non-safety kinds)
# ---------------------------------------------------------------------------

class LiveConnector(GenericConnector):
    """Generic live adapter; replace __getattr__ with typed, validated methods."""

    def __getattr__(self, method: str) -> Any:
        def call(**kwargs: Any) -> Dict[str, Any]:
            raise NotImplementedError(
                f"Live connector for {self.kind}.{method} is not wired in this "
                f"accelerator. Implement against the validated vendor client during "
                f"the engagement. Run with CONNECTOR_MODE=fixture for the demo."
            )
        return call


# ---------------------------------------------------------------------------
# Live Safety connector -- real HTTP round-trip
# ---------------------------------------------------------------------------

def _get_safety_token() -> str:
    """Resolve the safety API bearer token (env var or Secrets Manager)."""
    from hcls_agent_platform.secrets import get_secret
    token = get_secret("safety_api_token", default="")
    return token or ""


def _safety_request(
    method: str,
    path: str,
    body: Any = None,
    base_url: str = "",
    token: str = "",
) -> Any:
    """Stdlib-only HTTP helper. Raises on non-2xx status. Returns parsed JSON."""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = _urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with _urllib_request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
    except URLError as exc:
        raise RuntimeError(
            f"Safety API call failed [{method} {url}]: {exc}"
        ) from exc


class LiveSafetyConnector(SafetyConnector):
    """
    Real HTTP connector for kind='safety'.

    Endpoint contract (reference_safety_service.py + real Argus/Veeva adapter):
        GET  /cases/{id}              -> case json
        POST /cases/search-duplicates -> list[{case_id, match_score, fields}]
        POST /cases/drafts            -> {case_id, status, written, ...}
        POST /reports                 -> {submission_id, gateway, status, ...}
    """

    kind = "safety"

    def __init__(self, base_url: str = "", token: str = "") -> None:
        self._base_url = base_url or os.getenv("SAFETY_BASE_URL", "")
        self._token = token  # empty -> resolved lazily per-call

    def _tok(self) -> str:
        return self._token or _get_safety_token()

    def get_case(self, case_id: str = "ICSR-1", **_: Any) -> Dict[str, Any]:
        """GET /cases/{case_id} -- retrieve an existing ICSR case."""
        result = _safety_request(
            "GET", f"cases/{case_id}",
            base_url=self._base_url, token=self._tok(),
        )
        if isinstance(result, dict) and "valid" not in result:
            result["valid"] = True
        return result

    def search_duplicates(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """POST /cases/search-duplicates -- find potential duplicate ICSRs."""
        result = _safety_request(
            "POST", "cases/search-duplicates",
            body=kwargs,
            base_url=self._base_url, token=self._tok(),
        )
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("matches", result.get("candidates", [result]))
        return []

    def write_case_draft(self, **kwargs: Any) -> Dict[str, Any]:
        """POST /cases/drafts -- create/update a case draft (high-risk write)."""
        result = _safety_request(
            "POST", "cases/drafts",
            body=kwargs,
            base_url=self._base_url, token=self._tok(),
        )
        if isinstance(result, dict):
            result.setdefault("status", "DRAFT")
            result.setdefault("written", True)
        return result

    def submit_report(self, **kwargs: Any) -> Dict[str, Any]:
        """POST /reports -- submit ICSR to safety gateway (irreversible write)."""
        result = _safety_request(
            "POST", "reports",
            body=kwargs,
            base_url=self._base_url, token=self._tok(),
        )
        if isinstance(result, dict):
            result.setdefault("status", "QUEUED")
        return result
