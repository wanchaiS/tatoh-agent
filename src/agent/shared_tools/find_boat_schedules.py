from typing import List, Dict, Literal
from langchain.tools import tool

from utils.google_drive_client import read_spreadsheet_data

Location = Literal[
    "bangkok", "chumphon", "hua hin", "koh phangan", "koh samui", "koh tao", 
    "surat thani", "koh lanta", "koh phi phi", "krabi", "nakhon si thammarat", 
    "phuket", "railay"
]

def _clean_location(name: str) -> str:
    """
    Cleans a location name by removing pier details and parenthetical info.
    Example: 'Chumphon (Thung Makham Pier)' -> 'chumphon'
    """
    if not name:
        return ""
    return name.split("(")[0].strip().lower()

@tool
def find_boat_schedules(req_origin: Location, req_destination: Location) -> List[Dict]:
    """
    Find boat schedules from origin to destination. Use for 'when' or route advice.
    (Supports mapping Thai location names to English literals).
    
    RESPONSE GUIDANCE:
    Present results as a clear list. For each schedule, ALWAYS include:
    - Departure Time (from 'departure')
    - Pier/Location name (from 'from' and 'to')
    - Price (from 'price')
    Example: "07:00 from Chumphon (Thung Makham Noi Pier) - 750 THB"

    Note: young_children_price = 2-10y, infant_price = 0-1y
    """
    all_schedules = read_spreadsheet_data("/cooper-project/data/boat_schedules")
    
    # Normalize request inputs
    req_origin = req_origin.lower().strip()
    req_destination = req_destination.lower().strip()

    matches = []
    for schedule in all_schedules:
        schedule_from = _clean_location(schedule.get('from', ''))
        schedule_to = _clean_location(schedule.get('to', ''))
        
        # Match if the cleaned names are identical or one is contained in the other
        # Ensure we don't match against empty cells
        if schedule_from and schedule_to and \
           (req_origin in schedule_from or schedule_from in req_origin) and \
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

def _parse_price(price_str) -> int:
    if price_str is None:
        return 0
    try:
        return int(float(str(price_str)))
    except (ValueError, TypeError):
        return 0