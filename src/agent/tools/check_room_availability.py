import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from langchain.tools import tool
from utils.pms_client import get_room_availability
from utils.date_utils import format_date_ranges

@tool
def check_room_availability(guests: int, checkInDate: str, checkOutDate: str) -> Dict[str, Any]:
    """
    Find rooms when guests number, explicit check-in and check-out dates are provided.

    Args:
        guests: Number of guests
        checkInDate: Check-in date (YYYY-MM-DD)
        checkOutDate: Check-out date (YYYY-MM-DD)

    Returns:
        A dictionary with the following keys:
        - "perfect_match": A list of room objects (dictionaries) that match the guest count (perfect capacity) and the requested dates.
        - "date_matched_but_need_extension_bed": A list of room objects that match requested dates but require an extra bed (guests == max capacity + 1).
        - "alternatives": A list of room objects that were not date matched and/or room is too large.
        - "error": Optional error message if the input is invalid or metadata fails to load.
    """
    try:
        check_in_dt = datetime.strptime(checkInDate, '%Y-%m-%d')
        check_out_dt = datetime.strptime(checkOutDate, '%Y-%m-%d')
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    # 1. Fetch availability from PMS
    start_dates = _get_start_dates(check_in_dt, check_out_dt)
    room_availability_dict = {} 

    # Merge all availability from different 14 days windows  
    for start_date_str in start_dates:
        api_result = get_room_availability(start_date_str)

        for room_no, room_info in api_result.get('rooms', {}).items():
            dates = room_info.get('dates', [])
            if room_no not in room_availability_dict:
                room_availability_dict[room_no] = {**room_info,"dates": set(dates)}
            else:
                room_availability_dict[room_no]["dates"].update(dates)
    # 2. Load room metadata
    try:
        with open('data/room_list.json', 'r') as f:
            rooms = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load room metadata: {e}"}

    perfect_rooms_candidates = []
    date_match_with_extension_candidates = []
    alternatives_candidates = []
    
    for room in rooms:
        room_no = room['room_no']
        max_cap = room['max_capacity']
        room_info = room_availability_dict.get(room_no, {})
        room_info = {**room_info,
        "price_weekdays": room['price_weekdays'], 
        "price_weekends": room['price_weekends'],
        "price_festival": room['price_festival'],
        "capacity": room['max_capacity'],
        "dates": list(room_info['dates'])
        }

        # short circuit if room is too small
        if _is_room_too_small(guests, max_cap):
            continue

        # Determind the perfect room candidate
        is_perfect_cap = _is_perfect_room_size(guests, max_cap)
        room_available = is_available(room_no, check_in_dt, check_out_dt, room_availability_dict)
        if is_perfect_cap and room_available:
            perfect_rooms_candidates.append(room_info)
            continue
        
        if room_available and _can_fit_but_extension_required(guests, max_cap):
            date_match_with_extension_candidates.append(room_info)
            continue
        
        # for simplicity the rest of the rooms we just put them in alternatives
        if len(room_info['dates']) > 0:
            alternatives_candidates.append(room_info)
        
    # Filter perfect matches and date_match_with_extension_candidates by least gap within the room type
    perfect_match_rooms = []
    date_match_with_extension_rooms = []
    
    grouped_perfect_candidates = group_by_room_type(perfect_rooms_candidates)
    for type_id, candidates in grouped_perfect_candidates.items():
        if len(candidates) > 1:
            # find gap score, add only the one with least gap
            candidate_score_dict = {candidate['room_no']: calculate_gap_score(candidate, check_in_dt, check_out_dt) for candidate in candidates}
            least_score = min(candidate_score_dict.values())
            for candidate in candidates:
                if candidate_score_dict[candidate['room_no']] == least_score:
                    perfect_match_rooms.append({
                        "room_no": candidate['room_no'], 
                        "room_type_name": candidate['room_type_name'],
                        "price_weekdays": candidate.get('price_weekdays'),
                        "price_weekends": candidate.get('price_weekends'),
                        "price_festival": candidate.get('price_festival'),
                        "image_token": f"room_picture_{candidate['room_no']}" if os.path.exists(f"data/room_pictures/{candidate['room_no']}.jpg") else "",
                        "capacity": candidate.get('capacity')
                    })
        else:
            perfect_match_rooms.append({
                "room_no": candidates[0]['room_no'], 
                "room_type_name": candidates[0]['room_type_name'],
                "price_weekdays": candidates[0].get('price_weekdays'),
                "price_weekends": candidates[0].get('price_weekends'),
                "price_festival": candidates[0].get('price_festival'),
                "image_token": f"room_picture_{candidates[0]['room_no']}" if os.path.exists(f"data/room_pictures/{candidates[0]['room_no']}.jpg") else "",
                "capacity": candidates[0].get('capacity')
            })
            
    grouped_date_match_with_extension_candidates = group_by_room_type(date_match_with_extension_candidates)
    for type_id, candidates in grouped_date_match_with_extension_candidates.items():
        if len(candidates) > 1:
            # find gap score, add only the one with least gap
            candidate_score_dict = {candidate['room_no']: calculate_gap_score(candidate, check_in_dt, check_out_dt) for candidate in candidates}
            least_score = min(candidate_score_dict.values())
            for candidate in candidates:
                if candidate_score_dict[candidate['room_no']] == least_score:
                    date_match_with_extension_rooms.append({
                        "room_no": candidate['room_no'], 
                        "room_type_name": candidate['room_type_name'],
                        "price_weekdays": candidate.get('price_weekdays'),
                        "price_weekends": candidate.get('price_weekends'),
                        "price_festival": candidate.get('price_festival'),
                        "image_token": f"room_picture_{candidate['room_no']}" if os.path.exists(f"data/room_pictures/{candidate['room_no']}.jpg") else "",
                        "capacity": candidate.get('capacity') + 1
                    })
        else:
            date_match_with_extension_rooms.append({
                "room_no": candidates[0]['room_no'], 
                "room_type_name": candidates[0]['room_type_name'],
                "price_weekdays": candidates[0].get('price_weekdays'),
                "price_weekends": candidates[0].get('price_weekends'),
                "price_festival": candidates[0].get('price_festival'),
                "image_token": f"room_picture_{candidates[0]['room_no']}" if os.path.exists(f"data/room_pictures/{candidates[0]['room_no']}.jpg") else "",
                "capacity": candidates[0].get('capacity') + 1
            })
    
    alternatives_rooms = []
    for room in alternatives_candidates:
        alternatives_rooms.append({
            "room_no": room['room_no'], 
            "room_type_name": room['room_type_name'], 
            "price_weekdays": room.get('price_weekdays'),
            "price_weekends": room.get('price_weekends'),
            "price_festival": room.get('price_festival'),
            "image_token": f"room_picture_{room['room_no']}" if os.path.exists(f"data/room_pictures/{room['room_no']}.jpg") else "",
            "dates": format_date_ranges(room['dates']),
            "capacity": room.get('capacity')
        })

    need_alternatives = len(perfect_match_rooms) == 0 and len(date_match_with_extension_rooms) == 0
    need_date_match_with_extension_bed = len(perfect_match_rooms) == 0
    
    raw_data = {
        "perfect_match": perfect_match_rooms,
        "date_matched_but_need_extension_bed": date_match_with_extension_rooms if need_date_match_with_extension_bed else [],
        "alternatives": alternatives_rooms if need_alternatives else []
    }

    return raw_data

def group_by_room_type(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Groups a list of room numbers by their room_type_id."""
    grouped = {}
    for candidate in candidates:
        # Retrieve the room_type_id stored in room_availability_dict
        type_id = candidate.get("room_type_id", "Unknown")
        
        if type_id not in grouped:
            grouped[type_id] = []
        grouped[type_id].append(candidate)
    return grouped

# Helper to check if a room is available for a date range
def is_available(room_no: str, start_dt: datetime, end_dt: datetime, room_availability_dict: Dict[str, Dict[str, Set[str]]]) -> bool:
    curr = start_dt
    while curr < end_dt:
        date_str = curr.strftime('%Y-%m-%d')
        if date_str not in room_availability_dict.get(room_no, {}).get("dates", set()):
            return False
        curr += timedelta(days=1)
    return True

def calculate_gap_score(room_info: Dict[str, Any], start_dt: datetime, end_dt: datetime) -> int:
    """
    Calculates a gap score for a room.
    Lower is better (closer to no gap).
    Counts contiguous available days before and after the stay.
    """
    room_dates = room_info.get("dates", set())
    
    # Gap before
    gap_before = 0
    curr = start_dt - timedelta(days=1)
    while curr.strftime('%Y-%m-%d') in room_dates:
        gap_before += 1
        curr -= timedelta(days=1)
        
    # Gap after
    gap_after = 0
    curr = end_dt # checkOutDate is inclusive for availability check in this context? 
    # Wait, check_out_dt is the day they leave. The room is available on check_out_dt for the NEXT person.
    # So we check from end_dt onwards.
    while curr.strftime('%Y-%m-%d') in room_dates:
        gap_after += 1
        curr += timedelta(days=1)
        
    return gap_before + gap_after


def _is_perfect_room_size(guests: int, max_capacity: int) -> bool:
    """
    Determines if the room size is a 'perfect' match for the guest number.
    Perfect match is when the room can fit the guests and has at most 1 spare capacity.
    """
    return 0 <= max_capacity - guests <= 1

def _can_fit_but_extension_required(guests: int, max_capacity: int) -> bool:
    """
    Determines if an extra bed is needed (guests exceeds capacity by 1).
    """
    return guests == max_capacity + 1

def _is_room_too_small(guests: int, max_capacity: int) -> bool:
    """
    Determines if the room size is too small for the guest number.
    """
    return guests > max_capacity + 1

def _get_start_dates(check_in_dt: datetime, check_out_dt: datetime) -> List[str]:
    """
    Api returns 14 days from start_date.
    Returns list of start_dates to call the API to cover the entire stay.
    api_start_date is check_in - 1 day for flexibility.
    """
    fetch_dates = []
    # Start minus 1 day from check-in for flexibility
    current_start = check_in_dt - timedelta(days=1)
    fetch_dates.append(current_start.strftime('%Y-%m-%d'))
    
    # If the stay extends beyond 14 days from initial start, add more dates
    stay_end = check_out_dt
    window_end = current_start + timedelta(days=14)
    
    while window_end < stay_end:
        current_start = window_end
        fetch_dates.append(current_start.strftime('%Y-%m-%d'))
        window_end = current_start + timedelta(days=14)
        
    return fetch_dates
