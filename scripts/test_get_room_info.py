import sys
from pathlib import Path

# Add src to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(root_path / ".env")
except ImportError:
    pass

from agent.chat.tools.get_room_info import get_room_info, read_spreadsheet_data

def test_tool(room_number):
    print(f"--- Testing get_room_info with room_number: {room_number} ---")
    try:
        # First test the direct data read to see the real exception
        print("\nTesting read_spreadsheet_data directly...")
        rooms = read_spreadsheet_data("/cooper-project/data/rooms_info")
        print(f"Successfully read {len(rooms)} rooms.")
        if rooms:
            print(f"First room data keys: {list(rooms[0].keys())}")
            print(f"First room data sample: {rooms[0]}")
            
        # Then test the tool invocation
        print("\nTesting tool invocation...")
        result = get_room_info.invoke({"room_number": room_number})
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"\nCaught Exception:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test get_room_info tool")
    parser.add_argument("room_number", nargs="?", default="V1", help="Room number to look up")
    args = parser.parse_args()
    
    test_tool(args.room_number)
