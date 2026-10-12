# Agent task: add `send_to_printer.py`

## Goal

Add a small, standalone client script that sends the generated fixture-report PNG from this project to the Raspberry Pi thermal-printer HTTP daemon.

The current PNG output path is:

`output/fixture_report.png`

Do not use the old `last_report.png` path.

## Before changing anything

1. Read `AGENTS.md` and follow the repository's existing conventions.
2. Inspect the current project structure and relevant scripts, especially `thermal_renderer.py`, to confirm how output paths and configuration are handled.
3. Keep this change focused. Do not rewrite the renderer or alter fixture-fetching/filtering logic.

## Required behaviour

Create `send_to_printer.py` in the project's existing, appropriate location (normally the repository root, unless the project conventions indicate otherwise).

The script should:

- Send the PNG bytes to the Pi daemon using an HTTP `POST` to `/print`.
- Use `Content-Type: image/png`.
- Authenticate with `Authorization: Bearer <token>`.
- Read the daemon base URL from the environment variable `PRINT_DAEMON_URL`.
- Read the bearer token from the environment variable `PRINT_TOKEN`.
- Default to `output/fixture_report.png`.
- Accept an optional command-line path to a different PNG file, so the script can be reused for testing.
- Resolve the default image path relative to the project/script location, not the caller's current working directory. For a user-supplied relative path, use a clear, documented rule (preferably relative to the current working directory).
- Fail with a concise, useful message if the image does not exist, either environment variable is missing, or the URL is malformed.
- Use a finite HTTP timeout. Do not retry automatically: a timeout can occur after the printer has started printing, and retrying could create a duplicate print.
- Check the HTTP response. On success, report that the daemon accepted/completed the print job. On failure, show the HTTP status and a useful response message where possible.
- Handle connection errors and timeouts with a concise explanation.
- Keep the script import-safe: only perform network activity when run as a script, not when imported.
- Use the project's existing dependencies and conventions where practical. If an HTTP client dependency is not already installed or declared, prefer Python's standard library (`urllib`) rather than adding a new dependency solely for this script.
- Do not print the bearer token or include it in error output.

## Configuration

Document these environment variables in the project's existing configuration documentation, if there is a suitable place:

- `PRINT_DAEMON_URL`: base URL of the Pi daemon, `http://192.168.1.103:8765`. Use the Pi's actual LAN address (static reservation already made in router) in the local `.env` or shell environment.
- `PRINT_TOKEN`: the same bearer token configured in the Pi daemon's `.env`. To be entered by user, use example figure for now.

The client should construct the request URL by adding `/print` to the base URL, avoiding accidental duplicate slashes. Validate configuration sufficiently to give helpful errors, but do not over-engineer URL parsing.

Do not commit real secrets. If the repository has a `.env.example`, add placeholder values there only if that matches the project's conventions, and ensure `.env` remains ignored by Git.

## Scope boundaries

- Do not modify `thermal_renderer.py` to make it print automatically.
- Do not add a folder watcher, scheduled task, background daemon, or automatic retry.
- Do not create a pipeline/orchestration script that fetches fixtures, filters them, renders them, and prints them.
- Do not change PNG rendering, resizing, dithering, printer settings, or the Raspberry Pi daemon.
- Do not add a `/text` endpoint.
- Do not assume that a successful HTTP response guarantees the paper looks correct; this script only submits the image to the existing daemon.

## Acceptance checks

After implementation, provide a short summary of changed files and how to test the script. At minimum, verify:

1. Running without arguments uses `output/fixture_report.png`.
2. Passing an alternate PNG path uses that file.
3. Missing image/configuration produces a clear error and non-zero exit status.
4. The request uses `POST /print`, `Content-Type: image/png`, and `Authorization: Bearer ...`.
5. HTTP error responses, connection failures, and timeouts are handled without a traceback or automatic retry.
6. Importing the module does not send a request.

Do not attempt a real print unless explicitly asked. If practical, use a mocked/local test server to verify request construction and error handling.
