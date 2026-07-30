#!/usr/bin/env python3
"""WISMO dashboard bridge — static shell + proxied backend data on 8091."""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ROOT.mkdir(exist_ok=True)
HOST = "0.0.0.0"
PORT = 8091
BACKEND = "http://127.0.0.1:8081"


def log(msg: str) -> None:
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}", flush=True)


def backend_proxy(method: str, path: str, query: str = "", body: bytes = b"") -> tuple[int, bytes]:
    url = f"{BACKEND}{path}"
    if query:
        url += "?" + query
    headers = {"Accept": "application/json"}
    if body:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body if body else None, headers=headers, method=method.upper())
    with urlopen(req, timeout=10) as res:
        out = res.read()
    return res.status, out


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log(fmt % args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _serve_file(self, name: str):
        target = str((ROOT / name).resolve())
        if not Path(target).exists():
            self.send_response(404)
            self.end_headers()
            return
        data = Path(target).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _map_path(self, path: str) -> str:
        mapped = path.replace("/bi/", "/", 1)
        if mapped == "":
            mapped = "/"
        return mapped

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in {"/", "/dashboard"}:
            self._serve_file("index.html")
            return
        if path in {"/bi", "/bi/"}:
            self._serve_file("bi.html")
            return
        if path.startswith("/bi/") or path.startswith("/api/"):
            try:
                mapped = self._map_path(path)
                status, body = backend_proxy("GET", mapped, parsed.query)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json(502, {"error": str(e)})
            return
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        if path.startswith("/bi/") or path.startswith("/api/"):
            try:
                mapped = self._map_path(path)
                status, out = backend_proxy("POST", mapped, parsed.query, body)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)
            except Exception as e:
                self._json(502, {"error": str(e)})
            return
        return SimpleHTTPRequestHandler.do_POST(self)

    def _json(self, status: int, obj):
        data = json.dumps({"ok": status < 400, "data": obj}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class _HTTPServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()


def main() -> None:
    os.chdir(ROOT)
    server = _HTTPServer((HOST, PORT), Handler)
    log(f"WISMO dashboard bridge listening on {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
