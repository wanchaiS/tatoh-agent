import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from langchain.tools import tool
from utils.pms_client import get_room_availability
from utils.google_drive_client import read_spreadsheet_data, get_image_direct_link
from utils.date_utils import format_date_ranges

@tool
def check_room_availability(guests: int, check_in_date: str, check_out_date: str) -> Any:
    """
    Find available rooms for a given number of guests and exact check-in and check-out dates.
    This tool fetches live availability from the PMS
    Args:
        guests: Number of guests.
        check_in_date: Check-in date in YYYY-MM-DD format.
        check_out_date: Check-out date in YYYY-MM-DD format.

    Returns:
        A dictionary with:
        - "match_type": One of "PerfectMatch", "DatesMatchExtendBed", "DatesMatchLargeRoom", "DurationMatchAlternativeDates", or None.
        - "results": A list of structured data objects per room or None.
    """
    
    try:
        check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out_date, '%Y-%m-%d')

        # 1. Fetch availability from PMS with ±5 day buffer for flexibility
        fetch_start = check_in_dt - timedelta(days=5)
        fetch_end = check_out_dt + timedelta(days=5)
            
        api_result = get_room_availability(fetch_start, fetch_end)
        room_availability_dict = api_result.get('rooms', {})


        # 2. Load room metadata
        rooms = read_spreadsheet_data("/cooper-project/data/rooms_info")
        perfect_rooms_candidates = []
        dates_match_ext_bed_req_candidates = []
        dates_match_large_room_candidates = []
        duration_match_alternative_dates_candidates = []
        
        for room in rooms:
            room_no = room['room_name'].lower()

            if room_no not in room_availability_dict:
                continue
                
            candidate = room_availability_dict[room_no]
            candidate.update({
                "price_weekdays": room['price_weekdays'], 
                "price_weekends": room['price_weekends_holidays'],
                "price_ny_songkran": room['price_ny_songkran'],
                "max_guests": int(room['max_guests']),
                "image_token": f"!img[{get_image_direct_link(f'/cooper-project/data/rooms/{room_no}/overview')}]"
            })

            # Skip if room is too small
            if guests > candidate['max_guests'] + 1:
                continue
            
            # Skip if no dates available
            if len(candidate['dates']) == 0:
                continue
            
            # Skip if available dates is not enough to cover the duration
            duration = (check_out_dt - check_in_dt).days
            all_combos = _build_date_combos(candidate['dates'], duration)
            candidate['all_combos'] = all_combos

            # Not enough dates to cover the duration
            if len(all_combos) == 0:
                continue
            
            # Determine the candidate's category
            if _is_available_exact_dates(candidate['dates'], check_in_dt, check_out_dt):
                # exact dates matches and size is perfect
                if 0 <= candidate['max_guests'] - guests <= 1:
                    perfect_rooms_candidates.append(candidate)

                # exact dates matches but size is not perfect (with extend bed)
                elif guests == candidate['max_guests'] + 1:
                    dates_match_ext_bed_req_candidates.append(candidate)
                else:
                    # exact dates matches but room is too large
                    dates_match_large_room_candidates.append(candidate)
            elif _is_available_alt_dates(all_combos, duration):
                # alternative dates matches
                duration_match_alternative_dates_candidates.append(candidate) 
            
        # Filter candidates by least gap within the room type to minimize fragmentation
        perfect_match = _filter_best_score(perfect_rooms_candidates, check_in_dt, check_out_dt)
        dates_match_ext_bed_req = _filter_best_score(dates_match_ext_bed_req_candidates, check_in_dt, check_out_dt)
        dates_match_large_room = _filter_best_score(dates_match_large_room_candidates, check_in_dt, check_out_dt)
        duration_match_alternative_dates = duration_match_alternative_dates_candidates

        # Group candidates for better UX (combine identical availability)
        p_grouped = _group_candidates_by_type_and_dates(perfect_match)
        e_grouped = _group_candidates_by_type_and_dates(dates_match_ext_bed_req)
        l_grouped = _group_candidates_by_type_and_dates(dates_match_large_room)
        a_grouped = _group_candidates_by_type_and_dates(duration_match_alternative_dates)

        # Exclusive prioritization logic
        if p_grouped:
            return {
                "match_type": "PerfectMatch",
                "results": [_get_room_data_object("PerfectMatch", c, check_in_dt, check_out_dt, guests) for c in p_grouped],
            }
        
        if e_grouped:
            return {
                "match_type": "DatesMatchExtendBed",
                "results": [_get_room_data_object("DatesMatchExtendBed", c, check_in_dt, check_out_dt, guests) for c in e_grouped],
            }
        
        if l_grouped:
            return {
                "match_type": "DatesMatchLargeRoom",
                "results": [_get_room_data_object("DatesMatchLargeRoom", c, check_in_dt, check_out_dt, guests) for c in l_grouped],
            }
        
        if a_grouped:
            return {
                "match_type": "DurationMatchAlternativeDates",
                "results": [_get_room_data_object("DurationMatchAlternativeDates", c, check_in_dt, check_out_dt, guests) for c in a_grouped],
            }
        
        return {"match_type": None, "results": None}

    except Exception as e:
        return {"error": str(e)}

def _is_holiday(dt: datetime) -> bool:
    """Checks if a date is a New Year or Songkran holiday."""
    # New Year: Dec 25 to Jan 5
    if (dt.month == 12 and dt.day >= 25) or (dt.month == 1 and dt.day <= 5):
        return True
    # Songkran: April 10 to April 17
    if dt.month == 4 and 10 <= dt.day <= 17:
        return True
    return False

def _is_weekend(dt: datetime) -> bool:
    """Checks if a date is a weekend (Friday, Saturday, Sunday)."""
    return dt.weekday() in [4, 5, 6] # 4=Friday, 5=Saturday, 6=Sunday

def _calculate_total_price(room: Dict[str, Any], start_dt: datetime, end_dt: datetime, guests: int) -> Dict[str, Any]:
    """Calculates the total price and structured breakdown for the stay."""
    total = 0
    breakdown_counts = {"Weekday": 0, "Weekend": 0, "Holiday": 0}
    breakdown_prices = {
        "Weekday": int(room.get('price_weekdays', 0)),
        "Weekend": int(room.get('price_weekends', 0)),
        "Holiday": int(room.get('price_ny_songkran', 0))
    }
    
    current = start_dt
    while current < end_dt:
        if _is_holiday(current):
            tier = "Holiday"
        elif _is_weekend(current):
            tier = "Weekend"
        else:
            tier = "Weekday"
            
        total += breakdown_prices[tier]
        breakdown_counts[tier] += 1
        current += timedelta(days=1)
        
    # Extra bed calculation
    extra_bed_info = None
    num_nights = (end_dt - start_dt).days
    if guests > room['max_guests']:
        extra_bed_total = 700 * num_nights
        total += extra_bed_total
        extra_bed_info = {
            "nights": num_nights,
            "rate": 700,
            "subtotal": extra_bed_total
        }
        
    breakdown_items = []
    for tier in ["Weekday", "Weekend", "Holiday"]:
        if breakdown_counts[tier] > 0:
            breakdown_items.append({
                "tier": tier,
                "nights": breakdown_counts[tier],
                "rate": breakdown_prices[tier],
                "subtotal": breakdown_counts[tier] * breakdown_prices[tier]
            })
            
    return {
        "total": total,
        "breakdown_items": breakdown_items,
        "extra_bed": extra_bed_info
    }

def _get_room_data_object(category: str, room: Dict[str, Any], check_in_dt: datetime, check_out_dt: datetime, guests: int) -> Dict[str, Any]:
    """Returns a structured data object for the room instead of a string."""
    room_type = room.get('room_type_name', 'Unknown Type')
    room_no = room.get('room_no', 'N/A').upper()
    image_token = room.get('image_token', '')
    max_guests = room.get('max_guests', 0)
    
    room_data = {
        "room_type": room_type,
        "room_no": room_no,
        "max_guests": max_guests,
        "request_guests": guests,
        "image_token": image_token,
        "category": category
    }

    if category == "DurationMatchAlternativeDates":
        room_data["available_ranges"] = format_date_ranges(room['all_combos'])
        room_data["nightly_rates"] = {
            "weekday": int(room.get('price_weekdays', 0)),
            "weekend": int(room.get('price_weekends', 0)),
            "holiday": int(room.get('price_ny_songkran', 0))
        }
    else:
        pricing = _calculate_total_price(room, check_in_dt, check_out_dt, guests)
        room_data.update({
            "total_price": pricing['total'],
            "price_breakdown": pricing['breakdown_items'],
            "extra_bed": pricing['extra_bed']
        })
        
    return room_data

def _group_candidates_by_type_and_dates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups rooms of the same type that share the exact same availability.
    Merges their room numbers into a comma-separated string.
    """
    if not candidates:
        return []
        
    grouped = {} # Key: (type_id, tuple_of_dates)
    
    for c in candidates:
        # Cast nested list all_combos to a tuple of tuples for hashability
        combos_tuple = tuple(tuple(combo) for combo in c['all_combos'])
        key = (c['room_type_id'], combos_tuple)
        
        if key not in grouped:
            # First room of this type/dates combo
            grouped[key] = dict(c) # Shallow copy
            # Ensure room_nos is a list of strings for joining later
            grouped[key]['room_nos'] = [c['room_no']]
        else:
            # Another room of the same type/dates
            grouped[key]['room_nos'].append(c['room_no'])
            
    # Finalize room_no strings
    result = []
    for item in grouped.values():
        item['room_no'] = ", ".join(sorted(item['room_nos']))
        result.append(item)
        
    return result


def _group_candidates_by_type(candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups candidates by their room_type_id."""
    grouped = {}
    for candidate in candidates:
        type_id = candidate.get("room_type_id", "Unknown")
        grouped.setdefault(type_id, []).append(candidate)
    return grouped

def _is_available_exact_dates(available_dates: List[str], check_in_dt: datetime, check_out_dt: datetime) -> bool:
    """
    Checks if all required nights of the stay are available in the room's dates.
    needed: from check_in up to (check_out - 1 day).
    """
    needed = []
    curr = check_in_dt
    while curr < check_out_dt:
        needed.append(curr.strftime('%Y-%m-%d'))
        curr += timedelta(days=1)
    
    return all(day in available_dates for day in needed)

# Helper to check if a room is available for a date range
def _is_available_alt_dates(all_combos: List[List[str]], duration: int) -> bool:
    for combo in all_combos:
        if len(combo) >= duration:
            return True
    return False

def _filter_best_score(candidates: List[Dict[str, Any]], start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    """
    Filters candidates to keep only the ones with the best (lowest) gap score within each room type.
    """
    if not candidates:
        return []

    grouped = _group_candidates_by_type(candidates)
    result = []

    for type_id, type_candidates in grouped.items():
        if len(type_candidates) > 1:
            # Calculate gap scores and find the minimum
            scores = {c['room_no']: _calculate_gap_score(c, start_dt, end_dt) for c in type_candidates}
            min_score = min(scores.values())
            # Keep all candidates that share the minimum score
            result.extend([c for c in type_candidates if scores[c['room_no']] == min_score])
        else:
            result.append(type_candidates[0])
            
    return result


# calculate gap score for a room with in the same room type
def _calculate_gap_score(room_info: Dict[str, Any], start_dt: datetime, end_dt: datetime) -> int:
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

