#!/usr/bin/env python3
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .service import (
    DEFAULT_AUDIT,
    build_gate_decision,
    execute_override,
    get_audit_events,
    run_pilot,
)

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "static" / "index.html"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            html = INDEX_HTML.read_text(encoding="utf-8").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if path == "/api/audit":
            self._send_json({"events": get_audit_events(DEFAULT_AUDIT)})
            return

        self._send_json({"error": "Not Found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        try:
            payload = self._read_json()

            if path == "/api/gate":
                blockers = int(payload.get("blockers", 0))
                warnings = int(payload.get("warnings", 0))
                score = payload.get("score")
                gate = build_gate_decision(blockers, warnings, score)
                self._send_json({"gate": gate})
                return

            if path == "/api/override":
                gate_report = payload["gate_report"]
                user = payload["user"]
                role = payload["role"]
                reason = payload["reason"]
                result = execute_override(gate_report, user, role, reason)
                self._send_json({"overridden": result})
                return

            if path == "/api/pilot":
                metrics = run_pilot(
                    dataset_path=Path("evaluation/pilot_dataset.jsonl"),
                    json_output=Path("evaluation/results.json"),
                    md_output=Path("evaluation/results.md"),
                )
                self._send_json({"metrics": metrics})
                return

            self._send_json({"error": "Not Found"}, status=404)

        except Exception as exc:  # pragma: no cover
            self._send_json({"error": str(exc)}, status=400)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = HTTPServer((host, port), Handler)
    print(f"UI running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
