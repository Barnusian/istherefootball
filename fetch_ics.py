import json
from pathlib import Path
from datetime import datetime, timezone

import requests
from icalendar import Calendar


# ----------------------------
# CONFIG
# ----------------------------

OUTPUT_DIR = Path("fixtures")
OUTPUT_FILE = OUTPUT_DIR / "fixtures.json"

ICS_SOURCES = {
    "Rangers": "https://www.skysports.com/calendars/football/fixtures/teams/rangers",
    "Celtic": "https://www.skysports.com/calendars/football/fixtures/teams/celtic",
    "Scotland": "https://www.skysports.com/calendars/football/fixtures/teams/scotland",
}


# ----------------------------
# HELPERS
# ----------------------------

def fetch_calendar(url):
    """
    Download ICS calendar data.
    """

    response = requests.get(url)

    response.raise_for_status()

    return response.text


def build_tags(home, away, venue, competition):
    """
    Generate useful tags for filtering/display.
    """

    tags = []

    teams = {home, away}

    # Team tags
    if "Rangers" in teams:
        tags.append("rangers")

    if "Celtic" in teams:
        tags.append("celtic")

    if "Scotland" in teams:
        tags.append("scotland")

    # Home/away tags
    if home == "Rangers":
        tags.append("rangers_home")

    if away == "Rangers":
        tags.append("rangers_away")

    # Old Firm
    if teams == {"Rangers", "Celtic"}:
        tags.append("old_firm")

    # Venue tags
    if venue == "Ibrox Stadium":
        tags.append("ibrox")

    if venue == "Hampden Park":
        tags.append("hampden")

    if venue == "Celtic Park":
        tags.append("celtic_park")

    # Competition tags
    if "UEFA" in competition:
        tags.append("european")

    if "Cup" in competition:
        tags.append("cup")

    if "Scottish Premiership" in competition:
        tags.append("league")

    if home == "Scotland" or away == "Scotland":
        tags.append("international")

    return sorted(set(tags))


def parse_summary(summary):
    """
    Convert:
    'Rangers v Celtic'

    into:
    ('Rangers', 'Celtic')
    """

    if " v " not in summary:
        return summary, ""

    home, away = summary.split(" v ", 1)

    return home.strip(), away.strip()


def extract_competition(description):
    """
    Attempt to extract competition name from description.
    """

    if not description:
        return "Unknown"

    parts = description.split(" - ")

    if len(parts) < 3:
        return "Unknown"

    return parts[2].strip()


def simplify_event(event):
    """
    Convert ICS VEVENT into local schema.
    """

    uid = str(event.get("UID"))

    summary = str(event.get("SUMMARY", "Unknown Fixture"))

    location = str(event.get("LOCATION", ""))

    description = str(event.get("DESCRIPTION", ""))

    start = event.decoded("DTSTART")

    # Convert to ISO UTC string
    if isinstance(start, datetime):
        start_iso = start.astimezone(timezone.utc).isoformat()
        timestamp = int(start.timestamp())
    else:
        start_iso = str(start)
        timestamp = 0

    home, away = parse_summary(summary)

    competition = extract_competition(description)

    tags = build_tags(
        home,
        away,
        location,
        competition
    )

    return {
        "fixture_id": uid,
        "start": start_iso,
        "timestamp": timestamp,
        "home": home,
        "away": away,
        "venue": location,
        "competition": competition,
        "description": description,
        "tags": tags,
    }


# ----------------------------
# MAIN
# ----------------------------

def main():

    OUTPUT_DIR.mkdir(exist_ok=True)

    all_fixtures = []

    seen_ids = set()

    for source_name, url in ICS_SOURCES.items():

        print()
        print(f"Fetching {source_name} calendar...")
        print(url)

        try:
            calendar_text = fetch_calendar(url)

            calendar = Calendar.from_ical(calendar_text)

        except Exception as error:
            print(f"Failed to fetch {source_name}: {error}")
            continue

        event_count = 0

        for component in calendar.walk():

            if component.name != "VEVENT":
                continue

            simplified = simplify_event(component)

            fixture_id = simplified["fixture_id"]

            # Avoid duplicates
            if fixture_id in seen_ids:
                continue

            seen_ids.add(fixture_id)

            all_fixtures.append(simplified)

            event_count += 1

        print(f"Added {event_count} fixtures")

    # Sort chronologically
    all_fixtures.sort(key=lambda x: x["timestamp"])

    # Write JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            all_fixtures,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("Done.")
    print(f"Saved {len(all_fixtures)} fixtures")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()