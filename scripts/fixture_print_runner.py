#!/usr/bin/env python3
"""Render the fixture report, then send it to the printer daemon."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_RENDERER = Path(__file__).resolve().with_name("image_renderer.py")
PRINTER_SCRIPT = Path(__file__).resolve().with_name("send_to_printer.py")
OUTPUT_IMAGE = PROJECT_ROOT / "output" / "fixture_report.png"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render a fixture report and send it to the printer."
    )
    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        help="number of days to include (defaults to the renderer's default)",
    )
    return parser.parse_args()


def print_output(output, stream):
    if output:
        print(output, end="" if output.endswith("\n") else "\n", file=stream)


def received_print_success(output):
    prefix = "Print accepted by daemon (HTTP 200): "
    for line in output.splitlines():
        if not line.startswith(prefix):
            continue
        try:
            response = json.loads(line[len(prefix):])
        except json.JSONDecodeError:
            continue
        if isinstance(response, dict) and response.get("status") == "printed":
            return True
    return False


def main():
    started_at = time.perf_counter()
    args = parse_args()

    render_command = [sys.executable, str(IMAGE_RENDERER)]
    if args.days is not None:
        render_command.append(str(args.days))

    render_result = subprocess.run(
        render_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    print_output(render_result.stdout, sys.stdout)
    print_output(render_result.stderr, sys.stderr)

    if render_result.returncode != 0:
        raise SystemExit(render_result.returncode)

    success_message = f"Report rendered to {OUTPUT_IMAGE}"
    if success_message not in render_result.stdout or not OUTPUT_IMAGE.is_file():
        print(
            "Error: image renderer did not confirm creating the fixture report.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    printer_result = subprocess.run(
        [sys.executable, str(PRINTER_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    print_output(printer_result.stdout, sys.stdout)
    print_output(printer_result.stderr, sys.stderr)

    if printer_result.returncode != 0:
        raise SystemExit(printer_result.returncode)
    if not received_print_success(printer_result.stdout):
        print(
            'Error: printer did not confirm HTTP 200 with {"status":"printed"}.',
            file=sys.stderr,
        )
        raise SystemExit(1)

    elapsed = time.perf_counter() - started_at
    print(f'Time to HTTP 200 {{"status":"printed"}}: {elapsed:.2f} seconds')


if __name__ == "__main__":
    main()
