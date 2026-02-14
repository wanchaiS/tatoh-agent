import sys
from pathlib import Path

# Add src to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path / "src"))

# Load environment variables if needed
try:
    from dotenv import load_dotenv
    load_dotenv(root_path / ".env")
except ImportError:
    pass

from agent.chat.tools.find_boat_schedules import find_boat_schedules

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test boat schedules tool")
    parser.add_argument("origin", help="Starting point (e.g., 'Chumphon', 'Koh Tao')")
    parser.add_argument("destination", help="Destination (e.g., 'Koh Tao', 'Surat Thani')")
    args = parser.parse_args()

    print(f"--- Boat Schedule Search ---")
    print(f"Origin:      {args.origin}")
    print(f"Destination: {args.destination}")
    print(f"----------------------------")

    try:
        # Lowercase inputs to match the Literal types expected by the tool
        origin_val = args.origin.lower().strip()
        dest_val = args.destination.lower().strip()
        
        # Call the tool function directly
        results = find_boat_schedules.invoke({"req_origin": origin_val, "req_destination": dest_val})
        
        if not results:
            print("\nNo schedules found. Check if the location names match those in the spreadsheet.")
        else:
            print(f"\nFound {len(results)} matching schedules:\n")
            for idx, item in enumerate(results, 1):
                # Using .get() with a default of 'N/A' but checking if value is None
                def val(k):
                    v = item.get(k)
                    return v if v is not None else "---"

                boat_type = val('type')
                departure = val('departure')
                arrival = val('arrival')
                price = val('price')
                child_price = val('young_children_price')
                infant_price = val('infant_price')
                notes = val('notes')
                vip = " (VIP)" if item.get('is_vip') else ""
                direct = " (Direct)" if item.get('is_direct') else ""

                print(f"[{idx}] {boat_type}{vip}{direct}")
                print(f"    {departure} -> {arrival}")
                print(f"    From: {val('from')}")
                print(f"    To:   {val('to')}")
                print(f"    Adult: {price} THB | Child: {child_price} THB | Infant: {infant_price} THB")
                if notes and notes != "---":
                    print(f"    Notes: {notes}")
                
                # Diagnostic help if everything is empty
                if all(item.get(k) is None for k in ['type', 'departure', 'arrival', 'from', 'to']):
                    print(f"    [!] This match has all empty fields. Available keys: {list(item.keys())}")
                
                print("-" * 20)
                
    except Exception as e:
        print(f"\nAn error occurred while running the tool:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        if "google_credentials.json" in str(e):
            print("\nTIP: Make sure 'google_credentials.json' is present in the project root.")
        elif "Spreadsheet not found" in str(e):
            print("\nTIP: Check if the spreadsheet path in find_boat_schedules.py is correct.")

if __name__ == "__main__":
    main()
