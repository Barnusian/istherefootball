"""Generate rolling 14-day fixture data and receipt images for the web UI."""

import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from image_renderer import ImageRenderer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
PRODUCER_SCRIPT = Path(__file__).resolve().with_name("produce_fixtures.py")
WEB_DATA_DIR = PROJECT_ROOT / "webui" / "data"
RECEIPTS_DIR = PROJECT_ROOT / "webui" / "static" / "receipts"
REPORT_DAYS = 14
WEEK_DAYS = 7


def get_fixtures_in_period(fixtures, start_date, days):
    """Return fixtures whose local start dates are in the requested period."""
    end_date = start_date + timedelta(days=days - 1)
    return [
        fixture
        for fixture in fixtures
        if start_date
        <= datetime.fromisoformat(fixture["start"]).date()
        <= end_date
    ]


def main():
    run_date = date.today()
    print(f"Generating web fixture reports from {run_date.isoformat()}...")
    subprocess.run(
        [sys.executable, str(PRODUCER_SCRIPT), str(REPORT_DAYS)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    source_path = FIXTURES_DIR / (
        f"short_fixtures_{run_date:%Y_%m_%d}_{REPORT_DAYS}day.json"
    )
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Fixture producer did not create its expected output: {source_path}"
        )

    with source_path.open("r", encoding="utf-8") as source_file:
        report_data = json.load(source_file)

    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    web_data_path = WEB_DATA_DIR / (
        f"web_fixtures_{run_date:%Y_%m_%d}_{REPORT_DAYS}day.json"
    )
    with web_data_path.open("w", encoding="utf-8") as output_file:
        json.dump(report_data, output_file, indent=4, ensure_ascii=False)
        output_file.write("\n")

    renderer = ImageRenderer()
    for week_index, image_name in enumerate(("this_week.png", "next_week.png")):
        start_offset = week_index * WEEK_DAYS
        week_start = run_date + timedelta(days=start_offset)
        week_fixtures = get_fixtures_in_period(
            report_data["fixtures"],
            week_start,
            WEEK_DAYS,
        )
        week_data = {
            "label": "THIS WEEK" if week_index == 0 else "NEXT WEEK",
            "generated_at": report_data["generated_at"],
            "fixtures": week_fixtures,
        }
        renderer.render_report(
            week_data,
            week_start,
            WEEK_DAYS,
            RECEIPTS_DIR / image_name,
            week_data["label"],
        )

    print(f"Web fixture data saved to {web_data_path}")


if __name__ == "__main__":
    main()
