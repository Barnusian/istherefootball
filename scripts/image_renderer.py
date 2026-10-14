import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# CONFIG
# ----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GET_FIXTURES_SCRIPT = Path(__file__).resolve().with_name("produce_fixtures.py")
SHORT_INPUT_DIR = PROJECT_ROOT / "fixtures"
OUTPUT_IMG = PROJECT_ROOT / "output" / "fixture_report.png"
WIDTH = 512
FONT_SIZE = 24
LINE_GAP = 8
REPORT_ART = (
    "FIXTURE REPORT",
    "     .------.",
    "   .' .--.   '.",
    "  /  /    \\   \\",
    " |  |      |   |",
    "  \\  \\    /   /",
    "   '. '--'  .'",
    "     '------'",
)
FONT_PATH_PAIRS = (
    (Path(r"C:\Windows\Fonts\consola.ttf"), Path(r"C:\Windows\Fonts\consolai.ttf")),
    (Path(r"C:\Windows\Fonts\cour.ttf"), Path(r"C:\Windows\Fonts\couri.ttf")),
    (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf"),
    ),
    (
        Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Italic.ttf"),
    ),
)

class ImageRenderer:
    def __init__(self):
        self.y = 0
        self.canvas = Image.new("1", (WIDTH, 4000), color=1)
        self.draw = ImageDraw.Draw(self.canvas)
        font_pair = next(
            (
                (regular, italic)
                for regular, italic in FONT_PATH_PAIRS
                if regular.is_file() and italic.is_file()
            ),
            None,
        )
        if font_pair is None:
            raise FileNotFoundError(
                "Could not find a supported monospaced font with an italic style."
            )
        font_path, italic_font_path = font_pair
        self.font = ImageFont.truetype(str(font_path), FONT_SIZE)
        self.italic_font = ImageFont.truetype(str(italic_font_path), FONT_SIZE)
        self.character_width = self.font.getlength("-")
        self.content_width_characters = int(
            (WIDTH - 4 * self.character_width) // self.character_width
        )
        self.content_left = (
            WIDTH - self.content_width_characters * self.character_width
        ) / 2
        self.content_right = (
            self.content_left
            + self.content_width_characters * self.character_width
        )
        self.separator = "-" * self.content_width_characters
        self.short_separator = "-" * 15
        self.font_ascent, self.font_descent = self.font.getmetrics()
        self.line_height = self.font_ascent + self.font_descent
        self.line_spacing = self.line_height + LINE_GAP

    def refresh_data(self, days):
        """Triggers the data provider script before rendering."""
        print(f"Refreshing data for {days} day(s)...")
        try:
            subprocess.run(
                [sys.executable, str(GET_FIXTURES_SCRIPT), str(days)],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error refreshing fixtures: {e}")
            sys.exit(1)

    def draw_grid_text(self, text, column, y, fill=0, font=None):
        self.draw.text(
            (
                self.content_left + column * self.character_width,
                y + self.font_ascent,
            ),
            text,
            fill=fill,
            font=font or self.font,
            anchor="ls",
        )

    def draw_centered_text(self, text, y, fill):
        left_characters = (self.content_width_characters - len(text)) // 2
        self.draw_grid_text(text, left_characters, y, fill)

    @staticmethod
    def truncate_team_name(name, max_characters):
        max_characters = min(17, max_characters)
        if len(name) <= max_characters:
            return name
        if max_characters <= 3:
            return "." * max_characters
        return name[: max_characters - 3] + "..."

    def draw_centered_team(self, name, y, left_label="", right_label=""):
        left_limit = len(left_label) + 1 if left_label else 0
        right_limit = (
            self.content_width_characters - len(right_label) - 1
            if right_label
            else self.content_width_characters
        )
        center_column = self.content_width_characters // 2
        max_centered_width = 2 * min(
            center_column - left_limit,
            right_limit - center_column,
        )
        max_characters = max(0, min(17, max_centered_width))
        display_name = self.truncate_team_name(name, max_characters)
        left_column = (self.content_width_characters - len(display_name)) // 2
        self.draw_grid_text(display_name, left_column, y)

    def draw_alert(self, text, column, y):
        horizontal_padding = self.character_width
        left = max(
            self.content_left,
            self.content_left
            + column * self.character_width
            - horizontal_padding,
        )
        top = y - 4
        right = min(
            self.content_right - 1,
            self.content_left
            + (column + len(text)) * self.character_width
            + horizontal_padding
        )
        bottom = y + self.line_height - 1
        self.draw.rectangle((left, top, right, bottom), fill=0)
        self.draw_grid_text(text, column, y, fill=1)

    def add_separator(self, separator):
        self.add_text(separator)

    def add_fixture(self, fixture, day_label=None):
        dt = datetime.fromisoformat(fixture["start"])
        tags = fixture["tags"]
        left_labels = []
        if day_label is not None:
            left_labels.append(day_label)
        if "ibrox" in tags:
            ibrox_alert = "IBROX"
        else:
            ibrox_alert = ""

        if left_labels:
            self.draw_grid_text(" ".join(left_labels), 0, self.y)
        self.draw_centered_team(
            fixture["home"],
            self.y,
            left_label=" ".join(left_labels),
            right_label=ibrox_alert,
        )
        if ibrox_alert:
            alert_column = (
                self.content_width_characters - len(ibrox_alert) - 1
            )
            self.draw_alert(ibrox_alert, alert_column, self.y)
        self.y += self.line_spacing

        time_text = dt.strftime("%H:%M")
        time_column = self.content_width_characters - len(time_text)
        self.draw_grid_text("v", (self.content_width_characters - 1) // 2, self.y)
        self.draw_grid_text(time_text, time_column, self.y)
        self.y += self.line_spacing

        if "old_firm" in tags:
            self.draw_alert("OLD FIRM", 1, self.y)
        self.draw_centered_team(fixture["away"], self.y)
        self.y += self.line_spacing

    def add_text(self, text):
        self.draw_centered_text(text, self.y, fill=0)
        self.y += self.line_spacing

    def add_date_range(self, start_date, days):
        weekday_names = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
        dates = [
            start_date + timedelta(days=offset)
            for offset in range(max(1, days))
        ]

        for offset in range(0, len(dates), 7):
            week = dates[offset : offset + 7]
            row_width = len(week) * 3 + (len(week) - 1) * 2
            first_column = (self.content_width_characters - row_width) // 2

            for index, current_date in enumerate(week):
                column = first_column + index * 5
                self.draw_grid_text(
                    weekday_names[current_date.weekday()],
                    column,
                    self.y,
                )
                self.draw_grid_text(
                    str(current_date.day),
                    column,
                    self.y + self.line_spacing,
                )

            self.y += 2 * self.line_spacing

    def render(self, days):
        # 1. Update data
        self.refresh_data(days)

        # 2. Load the specific slice of data
        short_input = SHORT_INPUT_DIR / (
            f"short_fixtures_{date.today():%m_%d}_{max(1, days)}day.json"
        )
        if not short_input.exists():
            print(f"Failed to find {short_input} after refresh.")
            return

        with open(short_input, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 3. Header
        self.y = 20
        for line in REPORT_ART:
            self.add_text(line)
        self.add_text(f"GLASGOW: {data['label']}")
        start_date = date.today()
        self.add_date_range(start_date, days)
        # 4. Content Logic
        self.add_separator(self.separator)

        fixtures_by_day = {}
        for fixture in sorted(
            data['fixtures'],
            key=lambda item: datetime.fromisoformat(item["start"]),
        ):
            fixture_date = datetime.fromisoformat(fixture["start"]).date()
            fixtures_by_day.setdefault(fixture_date, []).append(fixture)

        for day_offset in range(max(1, days)):
            fixture_date = start_date + timedelta(days=day_offset)
            fixtures = fixtures_by_day.get(fixture_date, [])
            if day_offset:
                self.add_separator(self.separator)

            if not fixtures:
                self.draw_grid_text(
                    fixture_date.strftime("%A").upper(),
                    0,
                    self.y,
                )
                self.draw_grid_text(
                    "STREETS ARE CLEAR",
                    13,
                    self.y,
                    font=self.italic_font,
                )
                self.y += self.line_spacing
                continue

            for fixture_index, fixture in enumerate(fixtures):
                if fixture_index:
                    self.add_separator(self.short_separator)

                day_label = (
                    fixture_date.strftime("%A").upper()
                    if fixture_index == 0
                    else None
                )
                self.add_fixture(fixture, day_label)

        # 5. Export
        final = self.canvas.crop((0, 0, WIDTH, self.y + 40))
        final.save(OUTPUT_IMG)
        print(f"Report rendered to {OUTPUT_IMG}")

if __name__ == "__main__":
    # Pull requested days from CLI, default to 7.
    try:
        requested_days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    except ValueError:
        print("Argument must be a number.")
        sys.exit(1)

    ImageRenderer().render(requested_days)