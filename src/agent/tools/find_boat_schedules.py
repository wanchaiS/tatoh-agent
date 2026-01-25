from typing import List, Dict
from utils.google_drive_client import read_spreadsheet_data
from langchain.tools import tool

def _clean_location(name: str) -> str:
    """
    Cleans a location name by removing pier details and parenthetical info.
    Example: 'Chumphon (Thung Makham Pier)' -> 'chumphon'
    """
    if not name:
        return ""
    return name.split("(")[0].strip().lower()

@tool
def find_boat_schedules(req_origin: str, req_destination: str) -> List[Dict]:
    """
    Find boat schedules from origin to destination. Use this when the user is asking for 'when' to get to Koh Tao or needs advice on routes.
    
    Returns a list of schedules with pricing fields:
    - from: origin location (whatever in the parenthesis is either a pier or bus stop)
    - to: destination location (whatever in the parenthesis is either a pier or bus stop)
    - departure: departure time
    - arrival: arrival time
    - type: type of the boat ("Catamaran", "Speedboat") Catamaran is a big boat, slower but more comfortable. Speedboat is a small boat, faster but less comfortable.than speed boats
    - price: Standard adult fare.
    - young_children_price: Applied for children aged 2 to 10 years.
    - infant_price: Applied for infants aged 0 to 1 year (typically free or discounted).
    - is_vip: Whether the bus (included service in the ticket) is for VIP type (larger seat, more comfortable).
    - is_direct: Whether the boat is a direct route.
    - notes: small details about the trip.
    
    Args:
        req_origin: The starting point (e.g., 'Chumphon', 'Koh Tao').
        req_destination: The destination (e.g., 'Koh Tao', 'Surat Thani').
    """
    all_schedules = read_spreadsheet_data("/cooper-project/data/boat_schedules")
    
    matches = []
    for schedule in all_schedules:
        schedule_from = _clean_location(schedule.get('from', ''))
        schedule_to = _clean_location(schedule.get('to', ''))
        
        # Match if the cleaned names are identical or one is contained in the other
        # This allows 'Chumphon' to match 'Chumphon City' if applicable
        if (req_origin in schedule_from or schedule_from in req_origin) and \
           (req_destination in schedule_to or schedule_to in req_destination):
        
            # format values
            schedule['is_vip'] = schedule.get('is_vip') == "TRUE"
            schedule['is_direct'] = schedule.get('is_direct') == "TRUE"
            
            # Convert price strings to integers/floats for calculations
            schedule['price'] = _parse_price(schedule.get('price', 0))
            schedule['infant_price'] = _parse_price(schedule.get('infant_price', 0))
            schedule['young_children_price'] = _parse_price(schedule.get('young_children_price', 0))
            
            matches.append(schedule)
    
    return matches

def _parse_price(price_str: str) -> int:
    try:
        return int(price_str)
    except ValueError:
        return 0