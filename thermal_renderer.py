import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# CONFIG
# ----------------------------
GET_FIXTURES_SCRIPT = "get_fixtures.py"
SHORT_INPUT = Path("fixtures/short_fixtures.json")
OUTPUT_IMG = Path("output/fixture_report.png")
WIDTH = 384

class ThermalRenderer:
    def __init__(self):
        self.y = 0
        self.canvas = Image.new("1", (WIDTH, 4000), color=1)
        self.draw = ImageDraw.Draw(self.canvas)

    def refresh_data(self, days):
        """Triggers the data provider script before rendering."""
        print(f"Refreshing data for {days} day(s)...")
        try:
            subprocess.run([sys.executable, GET_FIXTURES_SCRIPT, str(days)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error refreshing fixtures: {e}")
            sys.exit(1)

    def add_text(self, text, center=True):
        h = 15
        # Character-width math for Pillow's default font
        x = (WIDTH - (len(text) * 6)) // 2 if center else 10
        self.draw.text((x, self.y), text, fill=0)
        self.y += h + 5

    def add_alert(self, text):
        """Draws an inset black rectangle with white text (Gugon's Tweak)."""
        h = 30
        # Inset by 40px from each side
        self.draw.rectangle([40, self.y, WIDTH - 40, self.y + h], fill=0)
        x = (WIDTH - (len(text) * 6)) // 2
        self.draw.text((x, self.y + 8), text, fill=1)
        self.y += h + 10

    def render(self, days):
        # 1. Update data
        self.refresh_data(days)

        # 2. Load the specific slice of data
        if not SHORT_INPUT.exists():
            print("Failed to find short_fixtures.json after refresh.")
            return

        with open(SHORT_INPUT, "r") as f:
            data = json.load(f)

        # 3. Header
        self.y = 20
        self.add_text(f"GLASGOW: {data['label']}", center=True)
        self.add_text(datetime.now().strftime("%H:%M"), center=True)
        self.y += 10

        # 4. Content Logic
        if not data['fixtures']:
            self.add_text("STREETS ARE CLEAR!", center=True)
        else:
            for f in data['fixtures']:
                # Alert Priority Logic
                if "ibrox" in f['tags']:
                    self.add_alert("!! IBROX !!")
                elif "old_firm" in f['tags']:
                    self.add_alert("!! OLD FIRM !!")
                else:
                    # Simple divider for non-critical games
                    self.draw.line([(40, self.y), (WIDTH - 40, self.y)], fill=0)
                    self.y += 15
                
                dt = datetime.fromisoformat(f['start'])
                self.add_text(f"{dt.strftime('%a %d %b')} @ {dt.strftime('%H:%M')}")
                self.add_text(f"{f['home']} v {f['away']}")
                self.add_text(f"{f['venue']}")
                self.y += 10 # Breathing room after each entry

        # 5. Export
        final = self.canvas.crop((0, 0, WIDTH, self.y + 40))
        final.save(OUTPUT_IMG)
        print(f"Report rendered to {OUTPUT_IMG}")
        final.show()

if __name__ == "__main__":
    # Pull requested days from CLI, default to 1 (Today)
    try:
        requested_days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    except ValueError:
        requested_days = 1

    ThermalRenderer().render(requested_days)