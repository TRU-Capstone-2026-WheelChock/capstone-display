from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Capstone Display</title>
</head>
<body>
  <pre id="state">waiting...</pre>
  <script>
    setInterval(async () => {
      const r = await fetch('/state');
      if (r.status === 200) {
        const text = await r.text();
        try {
          document.getElementById('state').textContent =
            JSON.stringify(JSON.parse(text), null, 2);
        } catch {
          document.getElementById('state').textContent = text;
        }
      }
    }, 1000);
  </script>
</body>
</html>
"""


def _make_handler(get_latest_json: Callable[[], str | None]) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/state":
                payload = get_latest_json()
                if payload is None:
                    self.send_response(204)
                    self.end_headers()
                else:
                    body = payload.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            elif self.path == "/":
                body = _HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default access logs

    return _Handler


async def serve(
    host: str,
    port: int,
    get_latest_json: Callable[[], str | None],
    logger: logging.Logger,
) -> None:
    server = ThreadingHTTPServer((host, port), _make_handler(get_latest_json))
    logger.info("HTTP server is UP http://%s:%d/", host, port)
    await asyncio.to_thread(server.serve_forever)
