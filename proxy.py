
"""
=============================================================
  Ascendia AMS — Proxy Server
  Fixes the CORS issue between dashboard.html and Snipe-IT
=============================================================
  HOW TO USE:
  1. Run:   python3 proxy.py
  2. Open:  http://localhost:3000/dashboard.html
=============================================================
"""

import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN       = os.getenv("SNIPEIT_TOKEN", "")
SNIPEIT_URL = os.getenv("SNIPEIT_URL", "http://snipe-it.test")
PORT        = 8888


class ProxyHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silence noisy logs

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        self._proxy_request('POST')

    def do_PATCH(self):
        self._proxy_request('PATCH')

    def do_DELETE(self):
        self._proxy_request('DELETE')

    def _proxy_request(self, method):
        if not self.path.startswith('/api/'):
            self.send_response(404)
            self.end_headers()
            return
        target = f"{SNIPEIT_URL}{self.path}"
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length) if length else None
        try:
            req = urllib.request.Request(target, data=body, method=method, headers={
                "Authorization": f"Bearer {TOKEN}",
                "Accept":        "application/json",
                "Content-Type":  "application/json",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self._cors()
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        # ── Proxy API calls to Snipe-IT ──────────────────
        if self.path.startswith("/api/"):
            target = f"{SNIPEIT_URL}{self.path}"
            try:
                req = urllib.request.Request(target, headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Accept":        "application/json",
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(data)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self._cors()
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_response(502)
                self._cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # ── Serve static files (dashboard.html etc.) ─────
        return SimpleHTTPRequestHandler.do_GET(self)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")


if __name__ == "__main__":
    if not TOKEN:
        print("❌  No token found in .env file.")
        print("    Make sure SNIPEIT_TOKEN is set in ~/ascendia-ams/.env")
        exit(1)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"✅  Proxy running at http://localhost:{PORT}")
    print(f"    Snipe-IT: {SNIPEIT_URL}")
    print(f"    Open:     http://localhost:{PORT}/dashboard.html")
    print(f"    Press Control+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
