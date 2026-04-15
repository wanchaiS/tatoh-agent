from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from agent.services.accessors import room_availability_svc_from
from agent.services.room_availability import RoomAvailabilityService
from agent.services.room_cache import room_cache
from agent.services.room_schemas import DateRange
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import Command

from agent.services.room_service import room_service


def build_date_ranges(dates: List[str], duration: int) -> List[DateRange]:
    """Convert raw available dates into DateRange objects representing valid check-in windows.

    Groups consecutive dates and returns ranges where a stay of `duration` nights fits.
    """
    if not dates:
        return []
    sorted_dates = sorted(dates)
    # Group into consecutive runs
    groups: List[List[str]] = []
    current_group = [sorted_dates[0]]
    for i in range(1, len(sorted_dates)):
        prev = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            current_group.append(sorted_dates[i])
        else:
            groups.append(current_group)
            current_group = [sorted_dates[i]]
    groups.append(current_group)

    # Build DateRanges — each group that can fit `duration` nights
    ranges = []
    for group in groups:
        if len(group) >= duration:
            ranges.append(DateRange(start_date=group[0], end_date=group[-1]))
    return ranges


EXPANSION_STEPS = [0, 3, 5, 7]


@dataclass
class ToolRoomSearchResult:
    """Raw search result from PMS — room names + available dates"""
    rooms: dict[str, list[str]]
    start_date: str
    end_date: str
    duration_nights: int
    expanded_days: int

@tool
async def search_available_rooms(
    start_date: str,
    end_date: str,
    duration_nights: int,
    guest_no: int | None = None,
    requested_rooms: List[str] | None = None,
    requested_room_types: List[str] | None = None,
    runtime: ToolRuntime = None,
    config: RunnableConfig = None,
) -> Command:
    """
    Search for available rooms based on the given criteria.

    Args:
        start_date: Start date of the search window (YYYY-MM-DD).
        end_date: End date of the search window (YYYY-MM-DD).
        duration_nights: Number of nights for the stay.
        guest_no: Number of guests.
        requested_rooms: List of specific room numbers requested by the user.
        requested_room_types: List of room types requested by the user.
    """

    # Perferm validation on start date, end date
    dates_error = _validate_dates(start_date, end_date)
    
    if dates_error:
        return _tool_error(f"{dates_error}. Ask user to provide valid dates.", runtime.tool_call_id)

    if duration_nights is None:
        return _tool_error("duration_nights is required to perform room searches. Ask user to provide duration_nights.", runtime.tool_call_id)

    # Validate requested rooms (exact match)
    resolved_rooms = None
    if requested_rooms:
        resolved_rooms = []
        errors = []
        for room in requested_rooms:
            if await room_cache.is_valid_room_name(room):
                resolved_rooms.append(room)
            else:
                valid = await room_cache.get_room_names_str()
                errors.append(f"Room '{room}' not found. Available rooms: {valid}")
        if errors:
            return _tool_error('; '.join(errors), runtime.tool_call_id)

    # Validate requested room types (exact match)
    resolved_room_types = None
    if requested_room_types:
        resolved_room_types = []
        errors = []
        for rt in requested_room_types:
            if await room_cache.is_valid_room_type(rt):
                resolved_room_types.append(rt)
            else:
                valid_types = await room_cache.get_room_types_str()
                errors.append(f"Room type '{rt}' not found. Available types: {valid_types}")
        if errors:
            return _tool_error('; '.join(errors), runtime.tool_call_id)

    # Fetch DB rooms once for validation and capacity checks
    db_rooms = await room_service.get_all_rooms()
    rooms_lookup_room_name = {r.room_name.lower(): r for r in db_rooms}
    db_type_by_name = {r.room_name.lower(): r.room_type for r in db_rooms}

    # Perform search to find all rooms on those dates
    search_result = await _search_rooms(start_date, end_date, duration_nights, rooms_lookup_room_name, room_availability_svc_from(config))

    # Approach 1: specific rooms/types requested — filter and return (no window expansion)
    if resolved_rooms or resolved_room_types:
        rooms_filter_desc = _describe_room_filter(resolved_rooms, resolved_room_types)
        filtered = _filter_by_request(search_result, resolved_rooms, resolved_room_types, db_type_by_name)

        if not filtered:
            return _tool_error(
                f"No rooms available for {duration_nights} nights for {rooms_filter_desc} "
                f"between {start_date} and {end_date}. "
                f"Ask user if they want to try different dates or different rooms/room types.",
                runtime.tool_call_id,
            )

        result = ToolRoomSearchResult(
            rooms=filtered,
            start_date=start_date,
            end_date=end_date,
            duration_nights=duration_nights,
            expanded_days=0,
        )
        return Command(
            update={
                "messages": [ToolMessage(
                    content=f"Found {len(filtered)} room(s) for {duration_nights} nights "
                            f"for {rooms_filter_desc} between {start_date} and {end_date}.",
                    tool_call_id=runtime.tool_call_id,
                )],
                "tool_room_search_results": [result],
                "phase": "closing",
            }
        )

    # Approach 2: No specific rooms required
    # 1. Check if there are any rooms available for the given dates and duration
    # 2. If not, try to find rooms that can mix and match to accommodate the duration (require guest number)
    # 3. If still no rooms, extend the date window and go back to #1 until reached max window
    # 4. If still no rooms, give up and ask them to change the dates

    # guest_no is required for combination check — ask once before entering loop
    if not search_result.rooms and guest_no is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No rooms available for the full duration on these dates, but room combinations may work. guest_no is required to check. Ask the user how many guests, then re-call search_available_rooms with the same start_date, end_date, duration_nights, and the new guest_no.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    for expansion in EXPANSION_STEPS:
        # For expansion=0, reuse the already-fetched search_result
        if expansion > 0:
            effective_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=expansion)).strftime("%Y-%m-%d")
            effective_end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=expansion)).strftime("%Y-%m-%d")
            search_result = await _search_rooms(effective_start, effective_end, duration_nights, db_by_name)
        else:
            effective_start = start_date
            effective_end = end_date
        expanded_note = f" (window expanded by ±{expansion} days)" if expansion > 0 else ""

        # Step 1: Rooms found for full duration — return them
        if search_result.rooms:
            search_result.expanded_days = expansion
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Found {len(search_result.rooms)} room(s) for {duration_nights} "
                                    f"nights between {effective_start} and {effective_end}{expanded_note}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "tool_room_search_results": [search_result],
                    "phase": "closing"
                }
            )

        # Step 2: No full-duration rooms — check if combinations can accommodate guest_no
        search_result_w_1_night = await _search_rooms(effective_start, effective_end, 1, db_by_name)
        if guest_no is not None and _can_accommodate(list(search_result_w_1_night.rooms.keys()), db_by_name, guest_no):
            search_result_w_1_night.expanded_days = expansion
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"No single room available for the full {duration_nights} nights, "
                                    f"but found {len(search_result_w_1_night.rooms)} room(s) that can be combined to "
                                    f"accommodate {guest_no} guest(s) between {effective_start} and "
                                    f"{effective_end}{expanded_note}. "
                                    f"Each room allows +1 guest with an extension bed. "
                                    f"Let the user browse and pick the rooms they prefer.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "tool_room_search_results": [search_result_w_1_night],
                    "phase": "closing"
                }
            )

        # Step 3: Not enough capacity — continue to next expansion

    # Step 4: Exhausted all expansion steps — no rooms found at all
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"No rooms or combinations found for {duration_nights} nights "
                            f"between {start_date} and {end_date}, even after expanding the "
                            f"search window by ±{EXPANSION_STEPS[-1]} days. "
                            f"Ask user if they want to try different dates or fewer guests.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

async def _search_rooms(start_date: str, end_date: str, duration_nights: int, db_by_name: dict, availability_svc: RoomAvailabilityService) -> dict[str, list[str]]:
    """Search rooms from PMS. Returns raw room names + available dates."""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    room_availability = await availability_svc.get_availability(start_dt, end_dt)

    # Filter: rooms that exist in our DB and have enough consecutive dates
    qualified_rooms = {}
    for room_no, room_data in room_availability.items():
        if room_no.lower() in db_by_name and _has_enough_consecutive_dates(room_data["dates"], duration_nights):
            qualified_rooms[room_no] = room_data["dates"]

    return qualified_rooms


def _tool_error(msg: str, tool_call_id: str) -> Command:
    return Command(
        update={"messages": [ToolMessage(content=f"Error: {msg}", tool_call_id=tool_call_id)]}
    )

# ── Helpers ────────────────────────────

def _parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def _can_accommodate(room_names: list[str], db_by_name: dict, guest_no: int) -> bool:
    """Check if the total capacity of all rooms (max_guests+1 each) can accommodate guest_no."""
    total_capacity = 0
    for name in room_names:
        db_room = db_by_name.get(name.lower())
        if db_room:
            total_capacity += db_room.max_guests + 1
    return total_capacity >= guest_no

def _validate_dates(start_date: str, end_date: str) -> str:
    if start_date is None or end_date is None:
        return "start_date and end_date are required."
    
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    if not start_dt:
        return "Invalid start_date format. Must be YYYY-MM-DD."
    if not end_dt:
        return "Invalid end_date format. Must be YYYY-MM-DD."
    if end_dt <= start_dt:
        return "end_date must be after start_date."
    if start_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        return "start_date is in the past."
    return None


def _describe_room_filter(rooms: list[str] | None, types: list[str] | None) -> str:
    """Build a human-readable description from resolved room names and/or types."""
    parts = []
    if rooms:
        parts.append(', '.join(rooms))
    if types:
        parts.append(', '.join(types))
    return ' '.join(parts)


def _filter_by_request(
    all_rooms: dict[str, list[str]],
    resolved_rooms: list[str] | None,
    resolved_room_types: list[str] | None,
    db_type_by_name: dict[str, str],
) -> dict[str, list[str]]:
    """Filter search results to only rooms matching requested names or types."""
    result = {}
    for name, dates in all_rooms.items():
        if resolved_rooms and name in resolved_rooms:
            result[name] = dates
        elif resolved_room_types and db_type_by_name.get(name.lower()) in resolved_room_types:
            result[name] = dates
    return result


def _has_enough_consecutive_dates(dates: list[str], duration: int) -> bool:
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
