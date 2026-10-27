#!/usr/bin/env python3
"""DEMO fixture server for deploy-verify trials. Not part of the skill.

Usage: python3 demo_server.py <port>:<folder> [<port>:<folder> ...]

Serves each folder on 127.0.0.1:<port>, reading files fresh on every request (so a "deploy" that
copies files into the folder shows at once). Per folder:
  404.html     served with status 404 for missing paths (otherwise a bare server-default 404)
  _redirects   lines "<from> <to> <status>", for example "/about.html /about 308"
  _pretty      if present, "/about" serves about.html (pretty URLs, as some static hosts do)
Files starting with "_" are never served. Only GET and HEAD are answered. Standard library only.
"""
import http.server
import pathlib
import sys
import threading
import urllib.parse

QUIET = False
DEFAULT_404 = b"<html><body><h1>404 Not Found</h1><p>nginx</p></body></html>"


def handler_for(root):
    root = pathlib.Path(root).resolve()

    class H(http.server.BaseHTTPRequestHandler):
        server_version = "demo-host/1"

        def log_message(self, fmt, *args):
            if not QUIET:
                sys.stderr.write(f"[{self.server.server_address[1]}] {fmt % args}\n")

        def answer(self, body_wanted):
            path = urllib.parse.urlsplit(self.path).path
            redirects = root / "_redirects"
            if redirects.exists():
                for line in redirects.read_text().splitlines():
                    parts = line.split()
                    if len(parts) == 3 and parts[0] == path:
                        self.send_response(int(parts[2]))
                        self.send_header("Location", parts[1])
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
            rel = urllib.parse.unquote(path).lstrip("/")
            target = (root / rel).resolve()
            if root not in target.parents and target != root:
                target = root / "__nope__"
            if target.is_dir():
                target = target / "index.html"
            if not target.exists() and (root / "_pretty").exists() and not target.suffix:
                target = target.with_suffix(".html")
            if target.exists() and not target.name.startswith("_"):
                body, status = target.read_bytes(), 200
                ctype = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
                         ".txt": "text/plain; charset=utf-8", ".json": "application/json",
                         ".png": "image/png", ".svg": "image/svg+xml", ".xml": "application/xml",
                         ".ico": "image/x-icon"}.get(target.suffix, "application/octet-stream")
            else:
                page = root / "404.html"
                body = page.read_bytes() if page.exists() else DEFAULT_404
                status, ctype = 404, "text/html; charset=utf-8"
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if body_wanted:
                self.wfile.write(body)

        def do_GET(self):
            self.answer(True)

        def do_HEAD(self):
            self.answer(False)

    return H


def main():
    pairs = sys.argv[1:]
    if not pairs:
        print(__doc__)
        return 2
    servers = []
    for p in pairs:
        port, folder = p.split(":", 1)
        s = http.server.ThreadingHTTPServer(("127.0.0.1", int(port)), handler_for(folder))
        servers.append(s)
        threading.Thread(target=s.serve_forever, daemon=True).start()
        print(f"serving {folder} on http://127.0.0.1:{port}/", flush=True)
    threading.Event().wait()


if __name__ == "__main__":
    sys.exit(main())
