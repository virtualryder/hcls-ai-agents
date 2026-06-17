"""
Reference Safety Service — local REST stub for PV live-path testing.

A dependency-free http.server implementation that mimics a real ICSR / safety
database REST API (Argus Safety / Veeva Safety / Oracle Empirica style).
Designed so LiveSafetyConnector can make real HTTP round-trips without requiring
an actual vendor system.

Endpoints
---------
GET  /health                    -> {"status": "ok"}
GET  /cases/{id}                -> case JSON
POST /cases/search-duplicates   -> list of potential duplicate matches
POST /cases/drafts              -> created draft acknowledgement
POST /reports                   -> submission / E2B gateway acknowledgement

Usage
-----
Stand-alone:
    python reference_safety_service.py          # listens on SAFETY_PORT (default 8099)
    python reference_safety_service.py 9001     # explicit port

Embedded (used by demo_live.py and test_live_connector.py):
    from reference_safety_service import start_in_background, stop
    port = start_in_background()          # returns actual bound port
    ...
    stop()

Customer note: swap SAFETY_BASE_URL to your Argus/Veeva endpoint. No code
changes needed — the connector speaks the same REST contract.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# In-memory case store (mimics a real safety DB)
# ---------------------------------------------------------------------------

_CASES: Dict[str, Dict[str, Any]] = {
    "ICSR-2026-0001": {
        "case_id": "ICSR-2026-0001",
        "status": "OPEN",
        "valid": True,
        "patient_age": "52 years",
        "patient_sex": "FEMALE",
        "suspect_drug": "Metformin",
        "event_description": "nausea and vomiting",
        "reporter_name": "Dr. Jane Williams",
        "reporter_country": "United Kingdom",
        "is_serious": False,
        "created_at": "2026-01-10T09:00:00Z",
    },
    "ICSR-2026-0002": {
        "case_id": "ICSR-2026-0002",
        "status": "OPEN",
        "valid": True,
        "patient_age": "67 years",
        "patient_sex": "MALE",
        "suspect_drug": "Lisinopril",
        "event_description": "acute renal failure",
        "reporter_name": "Dr. Robert Chen",
        "reporter_country": "Canada",
        "is_serious": True,
        "seriousness_criteria": ["hospitalization"],
        "created_at": "2026-01-15T14:30:00Z",
    },
    "ICSR-2026-0003": {
        "case_id": "ICSR-2026-0003",
        "status": "CLOSED",
        "valid": True,
        "patient_age": "74 years",
        "patient_sex": "MALE",
        "suspect_drug": "Warfarin",
        "event_description": "intracranial haemorrhage",
        "reporter_name": "Johnson MK, Patel S",
        "reporter_country": "unspecified",
        "is_serious": True,
        "seriousness_criteria": ["death", "life_threatening"],
        "created_at": "2026-02-03T08:15:00Z",
    },
}

_DRAFTS: Dict[str, Dict[str, Any]] = {}
_SUBMISSIONS: Dict[str, Dict[str, Any]] = {}


def _duplicate_score(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Realistic duplicate-match scoring. Returns matches above 0.5 threshold
    when the incoming drug/event overlaps with known cases.
    """
    drug = (criteria.get("suspect_drug") or "").lower()
    event = (criteria.get("meddra_pt") or criteria.get("event_description") or "").lower()
    matches = []
    for case_id, case in _CASES.items():
        cd = (case.get("suspect_drug") or "").lower()
        ce = (case.get("event_description") or "").lower()
        score = 0.0
        if drug and cd and drug in cd:
            score += 0.45
        if event and ce and any(w in ce for w in event.split()):
            score += 0.35
        # Reporter country overlap
        rc = (criteria.get("reporter_country") or "").lower()
        cc = (case.get("reporter_country") or "").lower()
        if rc and cc and rc == cc:
            score += 0.15
        if score >= 0.5:
            matches.append({
                "case_id": case_id,
                "match_score": round(min(score, 0.99), 2),
                "fields": ["suspect_drug", "event_description"],
            })
    return matches


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class SafetyHandler(BaseHTTPRequestHandler):
    """Request handler for the reference safety service."""

    def log_message(self, fmt: str, *args: Any) -> None:  # suppress access log
        pass

    def _send_json(self, status: int, body: Any) -> None:
        payload = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _auth_ok(self) -> bool:
        """Accept any Bearer token (or no auth) for demo purposes."""
        auth = self.headers.get("Authorization", "")
        # In production this would validate the JWT/scoped token.
        # For the reference service we accept any bearer or no auth.
        return True  # always accept; swap for real validation in prod

    def do_GET(self) -> None:  # noqa: N802
        if not self._auth_ok():
            self._send_json(401, {"error": "unauthorized"})
            return

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # GET /health
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "reference-safety-service"})
            return

        # GET /cases/{id}
        m = re.match(r"^/cases/([^/]+)$", path)
        if m:
            case_id = m.group(1)
            if case_id in _CASES:
                self._send_json(200, _CASES[case_id])
            elif case_id in _DRAFTS:
                self._send_json(200, _DRAFTS[case_id])
            else:
                # Return a minimal case for any unknown id (mirrors permissive
                # real systems that return 200 with placeholder data for new IDs)
                self._send_json(200, {
                    "case_id": case_id,
                    "status": "OPEN",
                    "valid": True,
                    "note": "case not found in reference store; returning placeholder",
                })
            return

        self._send_json(404, {"error": f"not found: {self.path}"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth_ok():
            self._send_json(401, {"error": "unauthorized"})
            return

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        # POST /cases/search-duplicates
        if path == "/cases/search-duplicates":
            matches = _duplicate_score(body)
            self._send_json(200, matches)
            return

        # POST /cases/drafts
        if path == "/cases/drafts":
            draft_id = f"ICSR-DRAFT-{uuid.uuid4().hex[:8].upper()}"
            draft = {
                "case_id": draft_id,
                "status": "DRAFT",
                "written": True,
                "created_at": _now_iso(),
                "echo": body,
            }
            _DRAFTS[draft_id] = draft
            self._send_json(201, draft)
            return

        # POST /reports  (E2B gateway submission)
        if path == "/reports":
            ack_id = f"E2B-{uuid.uuid4().hex[:8].upper()}"
            ack = {
                "submission_id": ack_id,
                "gateway": "FDA-FAERS-E2B",
                "status": "QUEUED",
                "icsr_version": "E2B(R3)",
                "ack_timestamp": _now_iso(),
                "case_id": body.get("case_id", "UNKNOWN"),
            }
            _SUBMISSIONS[ack_id] = ack
            self._send_json(202, ack)
            return

        self._send_json(404, {"error": f"not found: {self.path}"})


# ---------------------------------------------------------------------------
# Server lifecycle helpers
# ---------------------------------------------------------------------------

_server_instance: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def start_in_background(port: int = 0, host: str = "127.0.0.1") -> int:
    """
    Start the reference safety service in a daemon thread.

    Pass port=0 to let the OS pick an ephemeral port (for tests).
    Returns the actual port the server is listening on.
    """
    global _server_instance, _server_thread

    server = HTTPServer((host, port), SafetyHandler)
    actual_port = server.server_address[1]
    _server_instance = server

    t = threading.Thread(target=server.serve_forever, name="RefSafetyService", daemon=True)
    t.start()
    _server_thread = t

    # Brief wait to ensure the socket is ready
    time.sleep(0.05)
    return actual_port


def stop() -> None:
    """Shut down the background server (call from test teardown)."""
    global _server_instance, _server_thread
    if _server_instance:
        _server_instance.shutdown()
        _server_instance = None
    _server_thread = None


def reset_store() -> None:
    """Reset in-memory store between tests."""
    _DRAFTS.clear()
    _SUBMISSIONS.clear()


# ---------------------------------------------------------------------------
# Stand-alone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv("SAFETY_PORT", "8099"))
    host = os.getenv("SAFETY_HOST", "127.0.0.1")
    print(f"[RefSafetyService] Listening on http://{host}:{port}/")
    print(f"[RefSafetyService] Endpoints: GET /health  GET /cases/{{id}}")
    print(f"[RefSafetyService]            POST /cases/search-duplicates")
    print(f"[RefSafetyService]            POST /cases/drafts   POST /reports")
    print(f"[RefSafetyService] Press Ctrl-C to stop.")
    server = HTTPServer((host, port), SafetyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[RefSafetyService] Stopped.")
