# AGENTS.md

## Project: Is There Football?

A small personal/home utility that answers:

> Is there a relevant football match happening in Glasgow, particularly around Ibrox?

The original idea was a public website, but the project has evolved into a local service for the people in the user's home. The eventual presentation may be a static HTML page, e-ink display, and/or thermal printer.

The user is not a football enthusiast and is specifically trying to avoid the disruption associated with football matches. Do not assume football knowledge on the user's part when explaining football-specific concepts.

---

## Core principle

Keep the project **small, understandable and reliable**.

This is not intended to become a football analytics application.

The project should:

1. Obtain fixture data from free public sources.
2. Maintain a local, simplified JSON representation.
3. Query that local data without repeatedly contacting external sources.
4. Tag fixtures according to their relevance.
5. Generate presentation formats from the local data.

Avoid unnecessary APIs, databases, frameworks, frontend tooling, or complex infrastructure.

---

## Current data source

Sky Sports provides public `.ics` calendar feeds.

### Rangers

`https://www.skysports.com/calendars/football/fixtures/teams/rangers`

### Celtic

`https://www.skysports.com/calendars/football/fixtures/teams/celtic`

### Scotland

`https://www.skysports.com/calendars/football/fixtures/teams/scotland`

These feeds are the current preferred fixture source.

Do not replace them with a paid football API unless explicitly requested.

The project previously used API-Football, but the user's free plan only exposed seasons through 2024, making it unsuitable for contemporary fixtures.

---

## Current architecture

The intended architecture is:

```text
Sky Sports ICS feeds
        |
        v
  fetch_ics.py
        |
        v
   fixtures.json
        |
        v
 query / report logic
        |
        +----------------+
        |                |
        v                v
      HTML          other outputs
                         |
                 +-------+-------+
                 |               |
                 v               v
              e-ink          thermal printer
```

The important architectural boundary is:

> `fixtures.json` is the local source of truth.

Presentation formats should not become dependencies of one another.

For example:

```text
JSON -> HTML
JSON -> thermal printer
JSON -> e-ink
```

is preferable to:

```text
JSON -> HTML -> thermal printer
```

---

# Existing files

## `fetch_ics.py`

Responsible for:

- downloading the three Sky Sports ICS feeds
- parsing the calendars
- extracting events
- simplifying the data
- adding tags
- deduplicating fixtures
- sorting chronologically
- writing `fixtures/fixtures.json`

It should not be responsible for presentation.

Dependencies currently used:

```text
requests
icalendar
python-dateutil
```

The script has already been successfully tested and produces fixture JSON.

---

## `fixtures/fixtures.json`

This is the local fixture cache.

A typical entry currently resembles:

```json
{
    "fixture_id": "f05d62622224a7d062b00d0a04cbc1b5@skysports.com",
    "start": "2025-08-31T11:00:00+00:00",
    "timestamp": 1756638000,
    "home": "Rangers",
    "away": "Celtic",
    "venue": "Ibrox Stadium",
    "competition": "Scottish Premiership",
    "description": "Rangers v Celtic - Ibrox Stadium - Scottish Premiership",
    "tags": [
        "celtic",
        "ibrox",
        "league",
        "old_firm",
        "rangers",
        "rangers_home"
    ]
}
```

Do not unnecessarily change this schema without discussing why.

---

## `game_on_date.py`

Current purpose:

- load `fixtures/fixtures.json`
- accept a date from the user
- find fixtures occurring on that date
- sort them by kickoff
- display them for debugging

The current input format is:

```text
YYYY-MM-DD
```

For example:

```text
2026-05-10
```

The eventual version should use today's date automatically, but manual date input is currently useful for testing historical fixtures.

---

# Fixture relevance

The project is interested in:

1. Rangers home games at Ibrox
2. Old Firm derbies
3. Scotland international games
4. Rangers away games
5. Celtic games

The exact ordering is primarily a human interpretation of importance, not necessarily something that needs to be encoded as a numerical priority.

The tagging system should carry the useful information.

Do not introduce a numerical priority/ranking system unless there is a concrete requirement for one.

---

# Current tags

The ingestion script currently creates tags including:

### Teams

```text
rangers
celtic
scotland
```

### Rangers location/status

```text
rangers_home
rangers_away
```

### Derbies

```text
old_firm
```

### Locations

```text
ibrox
hampden
celtic_park
```

### Competition/context

```text
european
cup
league
international
```

Tags are derived from the raw fixture information.

An Old Firm fixture must be recognised regardless of which team is listed as home.

For example, both:

```text
Rangers v Celtic
```

and:

```text
Celtic v Rangers
```

must receive:

```text
old_firm
```

Likewise, an Old Firm match at Hampden must still be considered an Old Firm fixture.

---

# Multiple fixtures on the same day

Never assume there can only be one relevant fixture per day.

The query layer should return a collection/list.

Fixtures on the same day should be ordered by kickoff time.

For example:

```text
12:00 Rangers v Celtic
15:00 Celtic v Aberdeen
19:45 Scotland v France
```

should remain three distinct events.

The eventual presentation layer should be able to display all relevant fixtures for a day or a wider period.

---

# Data refresh strategy

Fixture querying should **not** make requests to Sky Sports.

The intended pattern is:

```text
scheduled refresh
        |
        v
fetch_ics.py
        |
        v
local fixtures.json
        |
        v
queries use local JSON only
```

A daily scheduled run is currently considered sufficient.

The exact scheduling mechanism has not yet been implemented. On the user's home server, this may eventually be a cron job or another scheduler.

Do not add refresh logic to `game_on_date.py`.

The query layer should work entirely from the local cache.

---

# Historical testing

Historical fixture data is useful for testing the application logic.

The original API-Football implementation used:

```python
SEASON = 2025
```

but this is no longer relevant to the ingestion architecture.

The Sky Sports ICS feeds contain fixtures spanning the season, and the local JSON can be queried by date.

Historical queries are useful for testing:

- Old Firm tagging
- Rangers home matches
- Rangers away matches
- Celtic matches
- Scotland matches
- multiple fixtures on one day
- fixture ordering
- cup and European fixtures

---

# Presentation architecture

The user is considering generating a static HTML report.

This is a good fit because the eventual page can simply be served by the user's home server without requiring an application server or internet exposure.

However:

> HTML should not become the canonical output format.

The preferred architecture is:

```text
fixtures.json
      |
      v
report/query data
      |
      +------> HTML
      |
      +------> thermal printer
      |
      +------> e-ink
      |
      +------> CLI/debug output
```

A future report-building layer could produce a simple structured report such as:

```json
{
    "generated_at": "...",
    "period_start": "...",
    "period_end": "...",
    "fixtures": []
}
```

The exact report schema has not yet been finalised.

Do not prematurely introduce a complex model or framework.

---

# Static HTML

The likely HTML output will show a fixture report covering approximately the next week.

It should eventually be possible to host the generated file using a very lightweight static web server.

There is no current requirement for:

- Flask
- Django
- React
- Vue
- a database
- authentication
- a public-facing web service

The page may eventually be served only on the user's home network.

---

# Printer / e-ink outputs

These are future presentation targets.

They should consume the same underlying structured fixture/report data rather than parsing the HTML.

For example:

```text
fixtures.json
    |
    +--> HTML renderer
    |
    +--> printer renderer
    |
    +--> e-ink renderer
```

This keeps each output independent.

---

# External requests

Keep external requests confined to the ingestion process.

The normal operation of the system should look like:

```text
[scheduled]
fetch_ics.py
    |
    +--> Sky Sports
    |
    +--> fixtures.json

[on demand]
game/report/display
    |
    +--> fixtures.json
```

Do not make every display/query request contact Sky Sports.

---

# Code style and development approach

The user is learning Python while building this project.

Prefer:

- straightforward Python
- small functions
- descriptive variable names
- comments/docstrings where useful
- explicit code over clever abstractions
- standard library where practical
- minimal dependencies

When explaining code, explain what it does rather than simply replacing it with a more complicated implementation.

Avoid unnecessary "productionisation" for its own sake.

The user prefers to understand code line-by-line.

---

# Important terminology

The project uses:

- **fixture** = a scheduled football match
- **ingestion** = obtaining and normalising external fixture data
- **query** = asking the local JSON for fixtures matching a date/period
- **tag** = derived classification attached to a fixture
- **presentation layer** = something that turns structured data into HTML, terminal output, printer output, etc.

---

# Current next steps

The immediate development direction is:

1. Keep `fetch_ics.py` as the ingestion layer.
2. Keep `fixtures.json` as the local cache/source of truth.
3. Develop querying against the local JSON.
4. Extend querying from a single date to a useful upcoming period, probably seven days.
5. Create a structured report representation.
6. Generate static HTML from that report.
7. Later add printer/e-ink renderers using the same data.

Do not jump directly to the printer or e-ink implementation.

---

# Things explicitly rejected

Do not reintroduce these without a specific reason:

### Paid football APIs

The project is intentionally avoiding paid data services.

### API-Football

The free tier available to the user does not provide the contemporary season required.

### Direct querying from the presentation layer

The presentation layer should consume local data.

### Numerical match priority

Tags are currently considered sufficient.

### HTML as an intermediate data format

HTML is a presentation target, not the canonical data representation.

### Large web frameworks

This project should remain lightweight.

---

# Guiding principle

When making implementation decisions, favour:

```text
simple
local
scheduled
cached
structured
inspectable
```

over:

```text
real-time
remote
complex
over-engineered
```

The project exists to answer a very small practical question for a household:

> "Is there football nearby that we need to know about?"