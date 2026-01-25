from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain.tools import tool
from utils.pms_client import get_room_availability
from utils.google_drive_client import read_spreadsheet_data
from utils.date_utils import format_date_ranges

@tool
def find_available_windows(search_start: str, search_end: str, duration: int, guests: int) -> Dict[str, Any]:
    """
    Finds available rooms in given date windows for a specific duration and number of guests (max 31 days).
    
    Args:
        search_start: Start date of the search window (YYYY-MM-DD).
        search_end: End date of the search window (YYYY-MM-DD).
        duration: Desired length of stay in nights, used to qualify available rooms.
        guests: Number of guests, used to qualify available rooms.
        
    Returns:
        A list of rooms with available windows for the given duration and number of guests.
    """
    try:
        start_dt = datetime.strptime(search_start, '%Y-%m-%d')
        end_dt = datetime.strptime(search_end, '%Y-%m-%d')

        if duration <= 0:
            return {"error": "Duration must be at least 1 night."}

        # 1. Fetch Room Specs
        rooms_specs = read_spreadsheet_data("/cooper-project/data/rooms_info")

        # 2. Fetch PMS Availability with ±1 day buffer
        pms_data = get_room_availability(start_dt, end_dt)
        available_rooms = pms_data.get('rooms', {})

        req_duration = duration # Keep the input duration
        results = []

        for spec in rooms_specs:
            room_name = spec.get('room_name', '').lower()
            room_type = spec.get('room_type_name', 'Unknown Type')
            max_guests = int(spec.get('max_guests', 0))
            
            # Room Capacity Check (Allowing +1 for extra bed as in check_room_availability)
            if guests > (max_guests + 1):
                continue
                
            if room_name not in available_rooms:
                continue
            
            room_availability = available_rooms[room_name]

            # Build combos of dates that are consecutive and meet the duration
            all_combos = _build_date_combos(room_availability['dates'], req_duration)

            # Not enough dates to cover the duration
            if len(all_combos) == 0:
                continue

            # Determine category
            if max_guests == guests:
                category = "DurationMatchCapacityMatch"
                rank = 1
            elif (max_guests + 1) == guests:
                category = "DurationMatchRequireBedExtension"
                rank = 2
            else:
                category = "DurationMatchLargeRoom"
                rank = 3

            results.append({
                "rank": rank,
                "room_no": room_name.upper(),
                "room_type": room_type,
                "max_guests": max_guests,
                "request_guests": guests,
                "image_token": f"![room_picture:{room_name.lower()}]",
                "category": category,
                "available_ranges": format_date_ranges(all_combos),
                "nightly_rates": {
                    "weekday": int(spec.get('price_weekdays', 0)),
                    "weekend": int(spec.get('price_weekends_holidays', 0)),
                    "holiday": int(spec.get('price_ny_songkran', 0))
                }
            })

        # Sort by rank and pick top 5
        results.sort(key=lambda x: x['rank'])
        
        # Remove rank key from final output
        final_results = []
        for r in results[:5]:
            del r['rank']
            final_results.append(r)

        return {"results": final_results if final_results else []}
    except Exception as e:
        return {"error": str(e)}

def _is_available_alt_dates(all_combos: List[List[str]], duration: int) -> bool:
    for combo in all_combos:
        if len(combo) >= duration:
            return True
    return False

def _build_date_combos(room_dates: list[str], duration: int) -> List[List[str]]:
    """
    Identifies consecutive date sequences that meet the required duration.
    """
    if not room_dates:
        return []

    # Sort dates to correctly identify consecutive ranges
    sorted_dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in room_dates])
    
    all_combos = []
    cur_combo = []

    for i, current_dt in enumerate(sorted_dates):
        if not cur_combo:
            cur_combo.append(current_dt.strftime('%Y-%m-%d'))
            continue

        prev_dt = sorted_dates[i-1]
        if (current_dt - prev_dt).days == 1:
            cur_combo.append(current_dt.strftime('%Y-%m-%d'))
        else:
            if len(cur_combo) >= duration:
                all_combos.append(cur_combo)
            cur_combo = [current_dt.strftime('%Y-%m-%d')]
    
    if len(cur_combo) >= duration:
        all_combos.append(cur_combo)
    
    return all_combos