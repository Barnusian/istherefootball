# Is There Football?

A small local utility for checking football fixtures involving Rangers, Celtic
and Scotland, with particular attention to matches at Ibrox. The project can
fetch fixture data, save local JSON files, render a monochrome receipt-style PNG
and optionally submit that image to a thermal-printer daemon.

## Current workflow

The scripts can be run manually, and cron jobs are configured on the production
environment (RATBOX). The cron configuration lives on that system, not in this
repository, so it is not changed by updating or deploying repository files.

1. `scripts/fetch_ics.py` downloads the Rangers, Celtic and Scotland fixture
   calendars from Sky Sports, combines their events, removes duplicate event
   IDs, adds tags and saves a full-range JSON file in `fixtures/`.
2. `scripts/produce_fixtures.py` reads the most recently dated full-range JSON
   file and writes a JSON report containing fixtures for a rolling number of
   days starting today.
3. `scripts/image_renderer.py` runs the fixture producer, then renders that
   rolling report to `output/fixture_report.png`.
4. `scripts/fixture_print_runner.py` renders the report and submits the PNG to
   the configured printer daemon.

The configured cron jobs fetch fixtures daily and run the printer workflow on
Mondays. The commands can also be run manually. Fetching or rendering fixture
data does not by itself print it; printing is performed by the print runner or
by running `scripts/send_to_printer.py` directly.

## Setup

Use Python and install the dependencies listed in `requirements.txt`:

```text
python -m pip install -r requirements.txt
```

The image renderer also needs a monospaced regular and italic font available in
one of the paths it checks. It checks Consolas, Courier, DejaVu Sans Mono and
Liberation Mono locations for the current operating system.

To print, configure these variables in a project-root `.env` file or in the
process environment:

- `PRINT_DAEMON_URL`: the printer daemon's base HTTP or HTTPS URL.
- `PRINT_TOKEN`: the bearer token configured for that daemon.
- `WEBUI_HOST`: the interface to serve on (defaults to `0.0.0.0`, all IPv4
  interfaces; use `127.0.0.1` for local-only access).
- `WEBUI_PORT`: the web UI port (defaults to `8000`).

The `.env` file is ignored by Git. Do not commit printer credentials.

## Running the scripts

Run commands from the project root.

Fetch and save the full fixture data:

```text
python scripts/fetch_ics.py
```

Generate a rolling JSON report for today and the requested number of days:

```text
python scripts/produce_fixtures.py [days]
```

The number of days defaults to 7. A value of `1` means today only; `7` means
today plus the following six days. The report is saved in `fixtures/` as
`short_fixtures_YYYY_MM_DD_nday.json`, where the date is the generation date
and `n` is the number of days in the report.

Render the PNG (this also runs the producer and therefore requires a previously
fetched full-range fixture file):

```text
python scripts/image_renderer.py [days]
```

The number of days defaults to 7. The image is written to
`output/fixture_report.png`, replacing the previous report.

Render and submit the report to the printer daemon:

```text
python scripts/fixture_print_runner.py [days]
```

To submit an existing PNG without rendering a new one:

```text
python scripts/send_to_printer.py [path-to-image.png]
```

Without a path, the sender uses `output/fixture_report.png`. A relative path
provided on the command line is resolved from the current working directory.
The sender does not retry failed print requests.

Generate the two web receipt images and their source 14-day JSON report:

```text
python scripts/produce_web_fixtures.py
```

This runs the fixture producer with `14`, then saves
`webui/data/web_fixtures_YYYY_MM_DD_14day.json` and renders two images under
`webui/static/receipts/`: `this_week.png` contains the first seven days from the
run date, and `next_week.png` contains the following seven. These are rolling
7-day blocks, independent of the weekday. The script does not print either
image or change the configured cron jobs. It requires a previously fetched
full-range fixture file.

Preview the web UI and enable its receipt print buttons from the project root:

```text
python scripts/web_server.py
```

The server uses Flask and Waitress. On the server itself, open
`http://localhost:8000`; from another device on the network, open
`http://<server-LAN-IP>:8000`. Replace `8000` with your configured
`WEBUI_PORT` if you changed it. `WEBUI_HOST` defaults to `0.0.0.0` so other
devices can connect; use `127.0.0.1` to restrict it to the same machine.
Generate the web fixture images first so the receipts are available. The print
buttons send the selected PNG from the local server directly to the printer
daemon; the daemon URL and token remain server-side and use the same
`PRINT_DAEMON_URL` and `PRINT_TOKEN` configuration as
`scripts/send_to_printer.py`. If the result is ambiguous, check the printer
before retrying. Stop the server with Ctrl+C when finished.

## Data and report details

The full-range fixture file is named `long_fixtures_YYYY-MM-DD.json`. Fixture
entries include the event ID, ISO start time, timestamp, home and away teams,
venue, competition, description and derived tags. Tags identify relevant teams,
Rangers home/away status, Old Firm matches, selected venues and competition
context.

The rolling report JSON contains a label, generation time and a `fixtures` list.
The renderer orders fixtures by start time, groups them by date and indicates
days without fixtures. It highlights Ibrox and Old Firm matches in the report.
Each generated image includes one randomly selected header design from the
four text files in `text/`. The image is a 512-pixel-wide, monochrome
receipt-style PNG.

Generated fixture JSON files are ignored by Git. Keep a locally fetched
full-range file available before running the producer or renderer. The generated
web JSON and receipt PNGs are also ignored by Git.

## Scheduled Jobs

### First-time web UI deployment on RATBOX

The web UI is served by `scripts/web_server.py` using Flask and Waitress. It
binds to `WEBUI_HOST` (default `0.0.0.0`) and `WEBUI_PORT` (default `8000`).
The checked-in unit is
`deploy/systemd/istherefootball-web.service`. It runs as a system-wide systemd
service, managed by the system service manager and running with the unprivileged
`barnusian` account.

Connect to RATBOX, then clone the repository and install its dependencies:

```text
cd /home/barnusian
git clone https://github.com/Barnusian/istherefootball.git
cd /home/barnusian/istherefootball
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

Create `/home/barnusian/istherefootball/.env` with the web server and, if the
web UI's print buttons should be enabled, printer settings:

```text
PRINT_DAEMON_URL=https://printer-daemon.example
PRINT_TOKEN=replace-with-the-daemon-token
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000
```

Replace the example URL and token with the real printer configuration. Keep
this file private; it is ignored by Git. The web settings are optional and
default to `WEBUI_HOST=0.0.0.0` and `WEBUI_PORT=8000`.

The UI needs generated receipt images. On a new checkout, fetch fixtures first,
then generate the web images:

```text
.venv/bin/python scripts/fetch_ics.py
.venv/bin/python scripts/produce_web_fixtures.py
```

If an older `systemd --user` instance is installed, stop and disable it first
to avoid having two servers compete for the same port:

```text
systemctl --user disable --now istherefootball-web.service
```

Install the checked-in unit in the system service directory and enable it at
boot:

```text
sudo install -m 0644 deploy/systemd/istherefootball-web.service /etc/systemd/system/istherefootball-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now istherefootball-web.service
sudo systemctl status istherefootball-web.service
```

The system service manager starts this service at boot without requiring
`barnusian` to log in or enabling user lingering. The process itself runs as
`barnusian`, not root. View its logs with:

```text
sudo journalctl -u istherefootball-web.service -f
```

The UI is available on RATBOX at `http://localhost:8000` (or the configured
port). From another device on its network, open
`http://<RATBOX-LAN-IP>:8000`, replacing the port if configured differently.
An SSH tunnel is also available as an alternative:

```text
ssh -L 8000:127.0.0.1:8000 barnusian@RATBOX
```

Then open `http://localhost:8000` on that computer.

### Redeploying on RATBOX

After connecting to RATBOX, update the existing checkout and synchronize its
virtual environment:

```text
cd /home/barnusian/istherefootball
git status --short
git pull --ff-only
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

Check `git status --short` before pulling. If it shows local changes to tracked
files, resolve or preserve them before continuing; do not overwrite production
changes unintentionally. The `.env` file, fetched fixture data, generated
reports and logs are machine-local and should be kept in place. The cron
configuration is also managed on RATBOX and is not changed by `git pull`.

The cron jobs run their scripts directly from the checkout, so they need no
restart after an update. Refresh the installed system unit in case its
definition changed, then restart it to load updated code or configuration:

```text
sudo install -m 0644 deploy/systemd/istherefootball-web.service /etc/systemd/system/istherefootball-web.service
sudo systemctl daemon-reload
sudo systemctl restart istherefootball-web.service
sudo systemctl status istherefootball-web.service
```

If refreshed web receipts are needed, run
`.venv/bin/python scripts/produce_web_fixtures.py` before restarting; it
requires an existing full-range fixture file. Do not start a second server
process while the service is running.

The following cron entries are configured on the production environment
(RATBOX):

```
0 6 * * * cd /home/barnusian/istherefootball && /home/barnusian/istherefootball/.venv/bin/python /home/barnusian/istherefootball/scripts/fetch_ics.py >> /home/barnusian/istherefootball/logs/fetch_ics.log 2>&1
0 9 * * 1 cd /home/barnusian/istherefootball && /home/barnusian/istherefootball/.venv/bin/python /home/barnusian/istherefootball/scripts/fixture_print_runner.py
```

The first entry runs every day at 06:00 server time and appends standard output
and errors to `logs/fetch_ics.log`. The second is scheduled for Mondays at 09:00
server time. Cron configuration is held on RATBOX, outside this repository.

### Viewing and editing the crontab

Connect to RATBOX using SSH, then run these commands as the account that owns
the jobs:

```text
crontab -l
crontab -e
```

`crontab -l` displays that account's installed cron entries. `crontab -e`
opens them in the configured editor; save and exit to install the updated
crontab. Review the entries after editing with `crontab -l`. Do not edit cron's
spool files directly. These commands apply to the current account; use a
different account only when the jobs are intentionally owned by that account.

Cron uses the server's timezone unless configured otherwise. The five schedule
fields are minute, hour, day of month, month and day of week; `*` means every
value, and `1` in the last field means Monday on this system.

## Not implemented

The static companion UI displays the generated rolling **This Week** and **Next
Week** receipt images. It does not fetch fixture data or generate Monday-to-
Sunday calendar weeks. The Monday cron entry continues to invoke the existing
rolling-report print workflow, separately from the web images.
