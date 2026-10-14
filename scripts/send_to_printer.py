#!/usr/bin/env python3
"""Send a PNG fixture report to the Raspberry Pi thermal-printer daemon."""

import argparse
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
DEFAULT_IMAGE_PATH = PROJECT_ROOT / "output" / "fixture_report.png"


def resolve_image_path(path_value):
    """Resolve the PNG path.

    The default path is always relative to this project root. If the user passes a
    relative path, it is treated as relative to the current working directory.
    """
    if path_value is None:
        return DEFAULT_IMAGE_PATH

    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return candidate

    return (Path.cwd() / candidate).resolve()


def build_print_url(base_url):
    """Build the /print endpoint URL from the daemon base URL."""
    if not base_url:
        raise ValueError("PRINT_DAEMON_URL is not set.")

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "PRINT_DAEMON_URL is malformed. Use a full URL like "
            "http://192.168.1.103:8765"
        )

    return base_url.rstrip("/") + "/print"


def load_printer_config():
    """Read the daemon URL and bearer token from the environment."""
    base_url = os.environ.get("PRINT_DAEMON_URL", "").strip()
    token = os.environ.get("PRINT_TOKEN", "").strip()

    if not base_url:
        raise RuntimeError("Missing environment variable: PRINT_DAEMON_URL")

    if not token:
        raise RuntimeError("Missing environment variable: PRINT_TOKEN")

    return base_url, token


def send_image(image_path, base_url, token):
    """Upload the supplied PNG to the printer daemon."""
    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    print_url = build_print_url(base_url)
    payload = image_path.read_bytes()

    req = request.Request(
        print_url,
        data=payload,
        headers={
            "Content-Type": "image/png",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            status = getattr(response, "status", response.getcode())
            message = response.read().decode("utf-8", errors="replace").strip()
            if message:
                print(f"Print accepted by daemon (HTTP {status}): {message}")
            else:
                print(f"Print accepted by daemon (HTTP {status}).")

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        detail = body or "No response body returned."
        print(f"Printer request failed with HTTP {exc.code}: {detail}", file=sys.stderr)
        raise SystemExit(1) from None

    except (error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        print(f"Connection to printer daemon failed: {reason}", file=sys.stderr)
        raise SystemExit(1) from None


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Send a PNG report to the local Raspberry Pi thermal-printer daemon. "
            "By default this uses output/fixture_report.png."
        )
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        help=(
            "PNG file to print. Relative paths are resolved from the current "
            "working directory; the default path is output/fixture_report.png."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        image_path = resolve_image_path(args.image_path)
        base_url, token = load_printer_config()
        send_image(image_path, base_url, token)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
