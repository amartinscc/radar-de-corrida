"""Servidor HTTP mínimo de encurtamento de URLs (biblioteca padrão)."""
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("ENCURTADOR_PORT", "8080"))
BASE_URL = os.environ.get("ENCURTADOR_BASE_URL", f"http://localhost:{PORT}")
CACHE_TTL = int(os.environ.get("ENCURTADOR_CACHE_TTL", "300"))
_store: dict[str, str] = {}


def shorten(url: str) -> str:
    code = hashlib.sha256(url.encode()).hexdigest()[:7]
    _store[code] = url
    return f"{BASE_URL}/{code}"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/shorten":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        payload = json.dumps({"short_url": shorten(body["url"])}).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = _store.get(self.path.lstrip("/"))
        if url is None:
            self.send_error(404)
            return
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()


def run():
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    run()
