#!/usr/bin/env python3
"""Serve the fixture UI and its local receipt-print endpoint."""

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

if __package__:
    from .send_to_printer import load_printer_config, post_image, print_was_confirmed
else:
    from send_to_printer import load_printer_config, post_image, print_was_confirmed

WEB_ROOT = PROJECT_ROOT / "webui"
HOST = "127.0.0.1"
PORT = int(os.environ.get("WEBUI_PORT", "8000"))
ALLOWED_HOSTS = {f"localhost:{PORT}", f"{HOST}:{PORT}"}
RECEIPT_IMAGES = {
    name: WEB_ROOT / "static" / "receipts" / name
    for name in ("this_week.png", "next_week.png")
}


class WebRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/print":
            self.send_error(404)
            return

        if not self._is_local_same_origin():
            self._send_json(403, {"error": "Request must come from this UI."})
            return

        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Expected a JSON request."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"error": "Invalid request length."})
            return

        if content_length < 1 or content_length > 1024:
            self._send_json(400, {"error": "Invalid request size."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Invalid JSON request."})
            return

        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Invalid print request."})
            return

        image_name = payload.get("image")
        if not isinstance(image_name, str):
            self._send_json(400, {"error": "Unknown receipt image."})
            return
        image_path = RECEIPT_IMAGES.get(image_name)
        if image_path is None:
            self._send_json(400, {"error": "Unknown receipt image."})
            return
        if not image_path.is_file():
            self._send_json(404, {"error": "Receipt image is not available."})
            return

        try:
            base_url, token = load_printer_config()
            status, message = post_image(image_path, base_url, token)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            if 400 <= exc.code < 500:
                message = detail or f"Printer rejected the request (HTTP {exc.code})."
                self._send_json(502, {"error": message})
            else:
                self._send_json(
                    502,
                    {
                        "error": (
                            "Print outcome is unknown. Check the printer before "
                            "retrying."
                        )
                    },
                )
            return
        except FileNotFoundError as exc:
            self._send_json(404, {"error": str(exc)})
            return
        except (error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            self._send_json(
                502,
                {
                    "error": (
                        f"Print outcome is unknown ({reason}). Check the printer "
                        "before retrying."
                    )
                },
            )
            return
        except (RuntimeError, ValueError) as exc:
            self._send_json(503, {"error": str(exc)})
            return

        if not print_was_confirmed(status, message):
            detail = message or f"No response body returned (HTTP {status})."
            self._send_json(
                502,
                {
                    "error": (
                        f"Print outcome is unknown: {detail} Check the printer "
                        "before retrying."
                    )
                },
            )
            return

        self._send_json(200, {"message": f"Print confirmed by daemon: {message}"})

    def _is_local_same_origin(self):
        host = self.headers.get("Host", "")
        origin = urlsplit(self.headers.get("Origin", ""))
        return (
            host in ALLOWED_HOSTS
            and origin.scheme == "http"
            and origin.netloc == host
            and not origin.path
            and not origin.query
            and not origin.fragment
        )

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), WebRequestHandler)
    print(f"Serving fixture UI at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
