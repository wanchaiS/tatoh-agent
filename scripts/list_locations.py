import sys
from pathlib import Path

# Add src to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path / "src"))

from utils.google_drive_client import read_spreadsheet_data

def _clean_location(name: str) -> str:
    if not name:
        return ""
    return name.split("(")[0].strip().lower()

def main():
    try:
        all_schedules = read_spreadsheet_data("/cooper-project/data/boat_schedules")
        origins = set()
        destinations = set()
        
        for schedule in all_schedules:
            orig = schedule.get('from')
            dest = schedule.get('to')
            if orig:
                origins.add(_clean_location(orig))
            if dest:
                destinations.add(_clean_location(dest))
        
        print("UNIQUE ORIGINS (cleaned):")
        for o in sorted(list(origins)):
            if o: print(f"  - {o}")
            
        print("\nUNIQUE DESTINATIONS (cleaned):")
        for d in sorted(list(destinations)):
            if d: print(f"  - {d}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
