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
- `WEBUI_PORT`: the local web UI port (defaults to `8000`).

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

Then open `http://localhost:8000` in a browser, replacing `8000` with your
configured `WEBUI_PORT` if you changed it. Generate the web fixture images first
so the receipts are available. The print buttons send the selected PNG from the
local server directly to the printer daemon; the daemon URL and token remain
server-side and use the same `PRINT_DAEMON_URL` and `PRINT_TOKEN` configuration
as `scripts/send_to_printer.py`. If the result is ambiguous, check the printer
before retrying. Stop the local server with Ctrl+C when finished. To preview
without enabling printing, the files can still be served with
`python -m http.server 8000 --directory webui`; change `8000` to the desired
port.

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
