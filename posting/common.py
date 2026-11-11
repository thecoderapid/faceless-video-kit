"""Shared bits for the posting scripts: config.json, a one-shot local login redirect, HTTP error checks."""
import json
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.json"  # holds your tokens: it is in .gitignore, never commit or share it
PORT = 8765


def load():
    if not CONFIG.exists():
        sys.exit("No config.json yet: copy config.example.json to config.json and fill in your app keys.")
    return json.loads(CONFIG.read_text())


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")


def ok(r):
    """Raise on an HTTP error (or TikTok's 200-with-error body), else return the JSON body."""
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    body = r.json() if r.content and "json" in r.headers.get("content-type", "") else {}
    body = body if isinstance(body, dict) else {}
    err = body.get("error")
    if isinstance(err, dict) and err.get("code") not in (None, "ok"):
        raise RuntimeError(f"{err.get('code')}: {err.get('message')}")
    return body


def catch_redirect(auth_url, path="/"):
    """Open the browser on auth_url and wait for the single redirect back to http://127.0.0.1:PORT<path>."""
    got = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if not u.path.startswith(path):
                self.send_response(404)
                self.end_headers()
                return
            got.update({k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Connected. You can close this tab." if "code" in got else f"Failed: {got}"
            self.wfile.write(f"<h2 style='font-family:sans-serif'>{msg}</h2>".encode())

        def log_message(self, *a):
            pass

    HTTPServer.allow_reuse_address = False
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        sys.exit(f"Port {PORT} is busy (an earlier login still running?). Stop it and try again.")
    print("Opening the browser: log in with the account the videos should go to.")
    print(f"If it doesn't open, paste this URL into a browser:\n{auth_url}\n")
    webbrowser.open(auth_url)
    while not got:
        server.handle_request()
    server.server_close()
    return got
