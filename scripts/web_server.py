#!/usr/bin/env python3
"""Serve the fixture UI and its local receipt-print endpoint."""

import json
import os
from pathlib import Path
from urllib import error
from urllib.parse import urlsplit

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from waitress import serve

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

if __package__:
    from .send_to_printer import load_printer_config, post_image, print_was_confirmed
else:
    from send_to_printer import load_printer_config, post_image, print_was_confirmed

WEB_ROOT = PROJECT_ROOT / "webui"
HOST = os.environ.get("WEBUI_HOST", "0.0.0.0").strip() or "0.0.0.0"
PORT = int(os.environ.get("WEBUI_PORT", "8000"))
RECEIPT_IMAGES = {
    name: WEB_ROOT / "static" / "receipts" / name
    for name in ("this_week.png", "next_week.png")
}

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(WEB_ROOT, "index.html")


@app.get("/<path:filename>")
def web_file(filename):
    return send_from_directory(WEB_ROOT, filename)


@app.post("/api/print")
def print_receipt():
    if not _is_same_origin():
        return _send_json(403, {"error": "Request must come from this UI."})

    if request.mimetype != "application/json":
        return _send_json(415, {"error": "Expected a JSON request."})

    content_length = request.content_length
    if content_length is None:
        return _send_json(400, {"error": "Invalid request length."})
    if content_length < 1 or content_length > 1024:
        return _send_json(400, {"error": "Invalid request size."})

    try:
        payload = json.loads(request.get_data(cache=False))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _send_json(400, {"error": "Invalid JSON request."})

    if not isinstance(payload, dict):
        return _send_json(400, {"error": "Invalid print request."})

    image_name = payload.get("image")
    if not isinstance(image_name, str):
        return _send_json(400, {"error": "Unknown receipt image."})

    image_path = RECEIPT_IMAGES.get(image_name)
    if image_path is None:
        return _send_json(400, {"error": "Unknown receipt image."})
    if not image_path.is_file():
        return _send_json(404, {"error": "Receipt image is not available."})

    try:
        base_url, token = load_printer_config()
        status, message = post_image(image_path, base_url, token)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        if 400 <= exc.code < 500:
            message = detail or f"Printer rejected the request (HTTP {exc.code})."
            return _send_json(502, {"error": message})
        return _send_json(
            502,
            {
                "error": (
                    "Print outcome is unknown. Check the printer before retrying."
                )
            },
        )
    except FileNotFoundError as exc:
        return _send_json(404, {"error": str(exc)})
    except (error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return _send_json(
            502,
            {
                "error": (
                    f"Print outcome is unknown ({reason}). Check the printer "
                    "before retrying."
                )
            },
        )
    except (RuntimeError, ValueError) as exc:
        return _send_json(503, {"error": str(exc)})

    if not print_was_confirmed(status, message):
        detail = message or f"No response body returned (HTTP {status})."
        return _send_json(
            502,
            {
                "error": (
                    f"Print outcome is unknown: {detail} Check the printer "
                    "before retrying."
                )
            },
        )

    return _send_json(200, {"message": f"Print confirmed by daemon: {message}"})


def _is_same_origin():
    host = request.host
    origin = urlsplit(request.headers.get("Origin", ""))
    host_url = urlsplit(request.host_url)
    try:
        host_port = host_url.port
    except ValueError:
        return False
    if host_port is None:
        host_port = 80 if host_url.scheme == "http" else 443
    return (
        host_port == PORT
        and origin.scheme == "http"
        and origin.netloc == host
        and not origin.path
        and not origin.query
        and not origin.fragment
    )


def _send_json(status, payload):
    response = jsonify(payload)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response


def main():
    print(f"Serving fixture UI on {HOST}:{PORT}")
    serve(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
