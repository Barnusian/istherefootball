import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, date

# ----------------------------
# CONFIG
# ----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_FILE = PROJECT_ROOT / "fixtures" / "long_fixtures_*.json"

# ----------------------------
# DATA HANDLING
# ----------------------------

def load_fixtures():
    dated_files = []
    for path in FIXTURES_FILE.parent.glob(FIXTURES_FILE.name):
        try:
            file_date = date.fromisoformat(path.stem[len("long_fixtures_"):])
        except ValueError:
            continue

        if path.stem == f"long_fixtures_{file_date.isoformat()}":
            dated_files.append((file_date, path))

    if not dated_files:
        raise FileNotFoundError(f"Missing file matching: {FIXTURES_FILE}")

    _, latest_file = max(dated_files, key=lambda item: item[0])
    with open(latest_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_fixtures_in_range(fixtures, days_to_look_ahead):
    """
    Returns fixtures from today up to (and including) X days ahead.
    0 = Today only
    6 = Today plus next 6 days (a full week)
    """
    today = date.today()
    end_date = today + timedelta(days=days_to_look_ahead)
    
    results = []
    for fixture in fixtures:
        try:
            # Parse the ISO start string
            f_dt = datetime.fromisoformat(fixture["start"])
            f_date = f_dt.date()
        except (ValueError, KeyError):
            continue

        if today <= f_date <= end_date:
            results.append(fixture)
            
    # Sort chronologically
    results.sort(key=lambda x: x["start"])
    return results


# ----------------------------
# MAIN EXECUTION
# ----------------------------

def main():
    # 1. Load the data
    try:
        all_fixtures = load_fixtures()
    except Exception as e:
        print(f"Error: {e}")
        return

    # 2. Get the lookahead range from CLI or Prompt
    # Usage: python scripts/produce_fixtures.py 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Argument must be a number.")
            return
    else:
        days = 7

    # Adjusting logic: 
    # If user wants "1 day" (today), lookahead is 0. 
    # If user wants "7 days", lookahead is 6.
    lookahead = max(0, days - 1)
    
    matches = get_fixtures_in_range(all_fixtures, lookahead)

    # 3. Output for the user (or eventual pipe to Estrella/Pillow)
    date_label = "TODAY" if lookahead == 0 else f"NEXT {days} DAYS"
    
    print(f"\n--- GLASGOW FOOTBALL ALERT: {date_label} ---")
    
    if not matches:
        print("Quiet streets! No major games found.")
        return

    for f in matches:
        # Localize time for display
        dt = datetime.fromisoformat(f["start"])
        time_str = dt.strftime("%H:%M")
        date_str = dt.strftime("%a %d %b")
        
        # Highlight Ibrox for your specific avoidance needs
        alert = "!! IBROX !!" if "ibrox" in f["tags"] else ""
        
        print(f"{date_str} @ {time_str} | {f['home']} v {f['away']} {alert}")
        print(f"   Venue: {f['venue']}")
        print(f"   Tags:  {', '.join(f['tags'])}\n")

        # --- NEW: SAVE TO SHORT_FIXTURES.JSON ---
    output_data = {
        "label": date_label,
        "generated_at": datetime.now().isoformat(),
        "fixtures": matches
    }
    
    short_output = PROJECT_ROOT / "fixtures" / (
        f"short_fixtures_{date.today():%m_%d}_{lookahead + 1}day.json"
    )

    with open(short_output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Filtered {len(matches)} matches into {short_output}")

if __name__ == "__main__":
    main()