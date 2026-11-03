"""Local development proxy - only for testing the UI on a machine without Docker.

It reproduces what the nginx container does in Compose:
  * serves the files in web/ as static assets
  * forwards /api/* and /health to the backend service (default 127.0.0.1:8000)

It is NOT used by Docker or by CI; inside Compose the real nginx does this job.

Usage:  python3 scripts/dev_proxy.py [--port 8080] [--backend http://127.0.0.1:8000]
"""

import argparse
import functools
import http.server
import pathlib
import socketserver
import urllib.error
import urllib.request

WEB_DIR = pathlib.Path(__file__).resolve().parent.parent / "web"

# Never let the environment's HTTP_PROXY settings hijack a localhost call.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Handler(http.server.SimpleHTTPRequestHandler):
    backend = "http://127.0.0.1:8000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):  # noqa: N802 - http.server API
        if self.path.startswith("/api/") or self.path == "/health":
            self.proxy()
        else:
            super().do_GET()

    def proxy(self):
        url = self.backend + self.path
        try:
            with OPENER.open(url, timeout=5) as response:
                payload = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:  # noqa: BLE001
            message = f'{{"ok":false,"error":"proxy: {exc}"}}'.encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    def log_message(self, fmt, *args):
        print("[dev-proxy] " + fmt % args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    Handler.backend = args.backend
    handler = functools.partial(Handler)
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"dev proxy on http://127.0.0.1:{args.port} -> {args.backend} (root={WEB_DIR})")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
