from langchain_core.tools import tool
from datetime import datetime, timedelta
from typing import List, Optional, TypeAlias
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from agent.context.agent_service_provider import AgentServiceProvider
from agent.services.room_availability_service import RoomAvailabilityService
from agent.tools.common_validators import validate_dates, validate_room_names
from agent.tools.exceptions import ToolValidationError
from db.models import Room

EXPANSION_STEPS = [0, 3, 5, 7]

RoomAvailabilityResult: TypeAlias = dict[str, set[str]]

@tool
async def search_available_rooms(
    runtime: ToolRuntime[AgentServiceProvider],
    start_date: str,
    end_date: str,
    duration_nights: int,
    guest_no: Optional[int] = None,
    requested_rooms: Optional[List[str]] = None,
    requested_room_types: Optional[List[str]] = None,
):
    """
    Search for available rooms based on the given criteria.

    Args:
        start_date: Start date of the search window (YYYY-MM-DD).
        end_date: End date of the search window (YYYY-MM-DD).
        duration_nights: Number of nights for the stay.
        guest_no: Number of guests. Optional, only required for mix and match rooms.
        requested_rooms: List of specific room numbers requested by the user. Optional.
        requested_room_types: List of room types requested by the user. Optional.
    """
    # Prepare services
    room_availability_svc = runtime.context.room_availability

    internal_room_dict = runtime.state["rooms"]

    # Validate args
    validate_dates(start_date, end_date)

    if duration_nights is None:
        raise ToolValidationError("duration_nights is required to perform room searches. Ask user to provide duration_nights.")
   
    validate_room_names(internal_room_dict,requested_rooms,)
    _validate_room_types(internal_room_dict,requested_room_types)

    ### Searching process ###
    # Perform search to find all rooms on those dates
    search_result = await _search_rooms(start_date, end_date, duration_nights, internal_room_dict, room_availability_svc)

    # Approach 1: specific rooms/types requested — filter and return (no window expansion)
    if requested_rooms or requested_room_types:
        # Build room name -> type lookup dict for filtering
        room_name_room_type_lookup = {r.room_name.lower(): r.room_type.lower() for r in internal_room_dict.values()}
        filtered = _filter_by_requested_rooms_or_types(
            search_result, 
            requested_rooms, 
            requested_room_types, 
            room_name_room_type_lookup
        )   
        parts = []
        if requested_rooms:
            parts.append(f"room(s) {', '.join(requested_rooms)}")
        if requested_room_types:
            parts.append(f"type(s) {', '.join(requested_room_types)}")
        room_filter_desc = "for " + " and ".join(parts)

        if not filtered:
            return f"No rooms available for {duration_nights} nights {room_filter_desc} between {start_date} and {end_date}. Ask user if they want to try different dates or different rooms/room types."

        # found rooms
        return Command(update={
                "messages": [ToolMessage(
                    content=f"Found {len(filtered)} room(s) {room_filter_desc} for {duration_nights} nights between {start_date} and {end_date}.",
                    tool_call_id=runtime.tool_call_id,
                )],
                "pending_render_search_results": {"append": [filtered]},
                "pending_search_range": {"start": start_date, "end": end_date},
            })

    # Approach 2: No specific rooms required
    # 1. Check if there are any rooms available for the given dates and duration
    # 2. If not, try to find rooms that can mix and match to accommodate the duration (require guest number)
    # 3. If still no rooms, extend the date window and go back to #1 until reached max window
    # 4. If still no rooms, give up and ask them to change the dates


    for expansion in EXPANSION_STEPS:
        # For expansion=0, reuse the already-fetched search_result
        if expansion > 0:
            effective_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=expansion)).strftime("%Y-%m-%d")
            effective_end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=expansion)).strftime("%Y-%m-%d")
            search_result = await _search_rooms(effective_start, effective_end, duration_nights, internal_room_dict,room_availability_svc)
        else:
            effective_start = start_date
            effective_end = end_date
        expanded_note = f" (window expanded by ±{expansion} days)" if expansion > 0 else ""

        # Step 1: Rooms found for full duration — return them
        if search_result:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Found {len(search_result)} room(s) for {duration_nights} "
                                    f"nights between {effective_start} and {effective_end}{expanded_note}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "pending_render_search_results": {"append": [search_result]},
                    "pending_search_range": {"start": effective_start, "end": effective_end},
                }
            )
        # guest_no is required for combination check
        if guest_no is None:
            return """No rooms available for the full duration on {start_date} and {end_date},
            but room combinations may work. guest_no is required to check.
            Ask the user if they want to mix and match rooms, and pls provide the number of guests if they want mix and match"""

        # Step 2: No full-duration rooms — check if combinations can accommodate guest_no
        search_result_w_1_night = await _search_rooms(effective_start, effective_end, 1, internal_room_dict, room_availability_svc)
        if _can_accommodate(search_result_w_1_night, internal_room_dict, guest_no, effective_start, effective_end, duration_nights):
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Found {len(search_result_w_1_night)} room(s) that can be combined to accommodate {guest_no} guest(s) between {effective_start} and {effective_end}{expanded_note}. Let the user browse and pick the rooms they prefer.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "pending_render_search_results": {"append": [search_result_w_1_night]},
                    "pending_search_range": {"start": effective_start, "end": effective_end},
                }
            )

        # Step 3: Not enough capacity — continue to next expansion

    # Step 4: Exhausted all expansion steps — no rooms found at all
    return """
    No rooms or combinations found for {duration_nights} nights between {start_date} and {end_date}, 
    even after expanding the search window by ±{EXPANSION_STEPS[-1]} days. 
    Ask user if they want to try different dates.
    """

######################## Validators ################################

def _validate_room_types( internal_room_dict: dict[str, Room],room_types: Optional[list[str]] = None):
    if not room_types:
        return None

    invalid_types = []
    for room_type in room_types:
        if room_type.lower() not in [room.room_type.lower() for room in internal_room_dict.values()]:
            invalid_types.append(room_type)
    
    if invalid_types:
        valid = ", ".join(set(room.room_type for room in internal_room_dict.values()))
        raise ToolValidationError(f"Room type(s) {', '.join(invalid_types)} not found. Available room types: {valid}")

######################## Helpers ################################

async def _search_rooms(start_date: str, end_date: str, duration_nights: int, internal_room_dict: dict[str, Room], availability_svc: RoomAvailabilityService) -> RoomAvailabilityResult:
    """Search rooms from PMS. Returns raw room names + available dates."""
    room_availability = await availability_svc.get_availability(start_date, end_date)

    # Filter: rooms that exist internally and have enough consecutive dates
    qualified_rooms: RoomAvailabilityResult = {}
    for room_no, room_data in room_availability.items():
        if room_no.lower() in internal_room_dict and _has_enough_consecutive_dates(room_data["dates"], duration_nights):
            qualified_rooms[room_no] = room_data["dates"]

    return qualified_rooms


def _parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def _can_accommodate(
    rooms_with_dates: RoomAvailabilityResult,
    internal_room_dict: dict[str, Room],
    guest_no: int,
    effective_start: str,
    effective_end: str,
    duration_nights: int,
) -> bool:
    """
    Check if rooms can accommodate guest_no guests for duration_nights consecutive nights
    with exactly one room switch (caller has already ruled out no-switch options).

    For each possible duration_nights-length window within [effective_start, effective_end],
    try every split point k:
      - cap of rooms available every night in [0..k-1] >= guest_no (capacity = max_guests + 1)
      - AND cap of rooms available every night in [k..n-1] >= guest_no
    """
    start_dt = _parse_date(effective_start)
    end_dt = _parse_date(effective_end)
    if not start_dt or not end_dt:
        return False

    room_info = []
    for room_no, dates in rooms_with_dates.items():
        room = internal_room_dict.get(room_no.lower())
        if room:
            room_info.append((room.max_guests + 1, dates))

    if not room_info:
        return False

    d = start_dt
    while d + timedelta(days=duration_nights - 1) <= end_dt:
        window = [(d + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration_nights)]

        for split in range(1, duration_nights):
            p1, p2 = window[:split], window[split:]
            cap1 = sum(cap for cap, dates in room_info if all(nd in dates for nd in p1))
            cap2 = sum(cap for cap, dates in room_info if all(nd in dates for nd in p2))
            if cap1 >= guest_no and cap2 >= guest_no:
                return True

        d += timedelta(days=1)

    return False

def _filter_by_requested_rooms_or_types(
    all_rooms: RoomAvailabilityResult,
    requested_rooms: list[str] | None,
    requested_room_types: list[str] | None,
    room_name_room_type_mapping: dict[str, str],
) -> RoomAvailabilityResult:
    """Filter search results to only rooms matching requested names or types."""
    result = {}
    req_rooms_lower = [r.lower() for r in requested_rooms] if requested_rooms else []
    req_types_lower = [t.lower() for t in requested_room_types] if requested_room_types else []
    
    for name, dates in all_rooms.items():
        if requested_rooms and name.lower() in req_rooms_lower:
            result[name] = dates
        elif requested_room_types and room_name_room_type_mapping.get(name.lower()) in req_types_lower:
            result[name] = dates
    return result


def _has_enough_consecutive_dates(dates: set[str], duration: int) -> bool:
    """Check if there are at least `duration` consecutive dates."""
    if len(dates) < duration:
        return False
    sorted_dts = sorted(datetime.strptime(d, "%Y-%m-%d") for d in dates)
    run = 1
    for i in range(1, len(sorted_dts)):
        if (sorted_dts[i] - sorted_dts[i - 1]).days == 1:
            run += 1
            if run >= duration:
                return True
        else:
            run = 1
    return run >= duration