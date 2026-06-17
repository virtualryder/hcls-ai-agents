"""
Minimal HTTP server implementing the Bedrock AgentCore Runtime contract.

Uses only the stdlib so the image stays small and dependency-free at the server
layer. Routes:
    POST /invocations -> handler.invoke(payload)
    GET  /ping        -> handler.ping()

Run: python serve.py   (listens on 0.0.0.0:8080)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import handler as agent_handler

PORT = 8080


class AgentCoreHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):  # noqa: N802
        if self.path.rstrip("/") == "/ping":
            self._send(200, agent_handler.ping())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path.rstrip("/") != "/invocations":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, agent_handler.invoke(payload))
        except Exception as exc:  # fail closed with an error body
            self._send(500, {"error": type(exc).__name__, "detail": str(exc)})

    def log_message(self, *args):  # quiet default logging
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), AgentCoreHandler).serve_forever()
