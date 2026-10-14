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
FONT_PATHS = (
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path(r"C:\Windows\Fonts\cour.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
    Path("/System/Library/Fonts/Menlo.ttc"),
)

class ImageRenderer:
    def __init__(self):
        self.y = 0
        self.canvas = Image.new("1", (WIDTH, 4000), color=1)
        self.draw = ImageDraw.Draw(self.canvas)
        font_path = next((path for path in FONT_PATHS if path.is_file()), None)
        if font_path is None:
            raise FileNotFoundError("Could not find a supported monospaced font.")
        self.font = ImageFont.truetype(str(font_path), FONT_SIZE)
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

    def add_text(self, text):
        self.draw.text(
            (WIDTH // 2, self.y + self.font_ascent),
            text,
            fill=0,
            font=self.font,
            anchor="ms",
        )
        self.y += self.line_spacing

    def add_alert(self, text):
        """Draws an inset black rectangle with white text (Gugon's Tweak)."""
        horizontal_margin = WIDTH // 12
        self.draw.rectangle(
            [
                horizontal_margin,
                self.y,
                WIDTH - horizontal_margin,
                self.y + self.line_height - 1,
            ],
            fill=0,
        )
        self.draw.text(
            (WIDTH // 2, self.y + self.font_ascent),
            text,
            fill=1,
            font=self.font,
            anchor="ms",
        )
        self.y += self.line_spacing

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
        end_date = start_date + timedelta(days=max(1, days) - 1)
        date_format = "%a %d %b"
        if start_date == end_date:
            date_label = start_date.strftime(date_format)
        else:
            date_label = (
                f"{start_date.strftime(date_format)} - "
                f"{end_date.strftime(date_format)}"
            )
        self.add_text(date_label)
        # 4. Content Logic
        if not data['fixtures']:
            self.add_text("STREETS ARE CLEAR!")
        else:
            for f in data['fixtures']:
                # Alert Priority Logic
                if "ibrox" in f['tags']:
                    self.add_alert("!! IBROX !!")
                elif "old_firm" in f['tags']:
                    self.add_alert("!! OLD FIRM !!")
                else:
                    self.add_text("-" * 30)
                
                dt = datetime.fromisoformat(f['start'])
                self.add_text(f"{dt.strftime('%a %d %b')} @ {dt.strftime('%H:%M')}")
                self.add_text(f"{f['home']} v {f['away']}")
                self.add_text(f"{f['venue']}")

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