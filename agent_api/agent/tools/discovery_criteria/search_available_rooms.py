import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command


from db.models import Room
from agent.schemas import DateRange, Rates, RoomAvailability, RoomCard
from agent.services.room_availability import RoomAvailabilityService
from agent.services.room_service import room_service


EXPANSION_STEPS = [0, 3, 5, 7]

THAI_MONTHS = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]


def _make_window_label(start_date: str, end_date: str) -> str:
    """Human-readable Thai label for a search window, e.g. '11-13 พ.ค.' or '28 พ.ค. - 3 มิ.ย.'"""
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    if s.month == e.month and s.year == e.year:
        return f"{s.day}-{e.day} {THAI_MONTHS[s.month]}"
    return f"{s.day} {THAI_MONTHS[s.month]} - {e.day} {THAI_MONTHS[e.month]}"


@dataclass
class SearchResult:
    rooms: List[RoomCard]
    expanded_days: int
    exhausted: bool
    start_date: str
    end_date: str
    criteria_id: str
    label: str


def _parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _can_accommodate(rooms: List[RoomCard], guest_no: int) -> bool:
    """Check if the total capacity of all rooms (max_guests+1 each) can accommodate guest_no."""
    total_capacity = sum(r.max_guests + 1 for r in rooms)
    return total_capacity >= guest_no

def _validate_dates(start_date: str, end_date: str) -> str:
    if start_date is None or end_date is None:
        return "start_date and end_date are required."
    
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    if not start_dt:
        return f"Invalid start_date format. Must be YYYY-MM-DD."
    if not end_dt:
        return f"Invalid end_date format. Must be YYYY-MM-DD."
    if end_dt <= start_dt:
        return f"end_date must be after start_date."
    if start_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        return f"start_date is in the past."
    return None

@tool
async def search_available_rooms(
    start_date: str,
    end_date: str,
    duration_nights: int,
    guest_no: Optional[int] = None,
    requested_rooms: Optional[List[str]] = None,
    requested_room_types: Optional[List[str]] = None,
    runtime: ToolRuntime = None,
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

    # Error paths stay in criteria_discovery. Success paths transition to closing.
    base_update = {"phase": "criteria_discovery"}

    # Perferm validation on start date, end date
    dates_error = _validate_dates(start_date, end_date)
    if dates_error:
        return Command(
                update={**base_update,
                    "messages": [
                        ToolMessage(
                            content=f"Error: {dates_error}. Ask user to provide valid dates.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                }
            )

    if duration_nights is None:
        return Command(
            update={**base_update,
                "messages": [
                    ToolMessage(
                        content="Error: duration_nights is required to perform room searches. Ask user to provide duration_nights.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    # Resolve requested rooms (fuzzy match, case-insensitive)
    resolved_rooms = None
    if requested_rooms:
        resolved_rooms = []
        errors = []
        for room in requested_rooms:
            canonical, error = await room_service.resolve_room_name(room)
            if error:
                errors.append(error)
            else:
                resolved_rooms.append(canonical)
        if errors:
            return Command(update={**base_update,
                "messages": [ToolMessage(
                    content=f"Error: {'; '.join(errors)}",
                    tool_call_id=runtime.tool_call_id,
                )]
            })

    # Resolve requested room types (fuzzy match, case-insensitive)
    resolved_room_types = None
    if requested_room_types:
        resolved_room_types = []
        errors = []
        for rt in requested_room_types:
            canonical = await room_service.fuzzy_match_room_type(rt)
            if canonical:
                resolved_room_types.append(canonical)
            else:
                valid_types = await room_service.get_valid_rooms_list_str()
                errors.append(f"Room type '{rt}' not recognised. Valid types: {valid_types}")
        if errors:
            return Command(update={**base_update,
                "messages": [ToolMessage(
                    content=f"Error: {'; '.join(errors)}",
                    tool_call_id=runtime.tool_call_id,
                )]
            })

    # Perform search to find all rooms on those dates
    search_result = await search_rooms(start_date, end_date, duration_nights)

    # Approach 1 when requested rooms are provided, either found or not found, no window extension
    # If requested rooms/types provided, filter the search result using resolved canonical names
    if resolved_rooms or resolved_room_types:
        filtered_rooms = [
            room for room in search_result.rooms
            if (resolved_rooms and room.room_name in resolved_rooms)
            or (resolved_room_types and room.room_type in resolved_room_types)
        ]
        # If filtered rooms found, return them
        if filtered_rooms:
            pending_ui_item, search_result.label = _build_pending_ui(filtered_rooms, start_date, end_date, search_result.criteria_id)
            rooms_filter_desc = _describe_room_filter(resolved_rooms, resolved_room_types)

            return Command(
                update={**base_update,
                    "messages": [
                        ToolMessage(
                            content=f"Found {len(filtered_rooms)} room(s) for {duration_nights} "
                                    f"nights for {rooms_filter_desc} "
                                    f"between {start_date} and {end_date}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "pending_ui": [pending_ui_item],
                    "latest_search_results": [search_result],
                    "phase": "closing"
                }
            )
        # No rooms found for requested rooms/types
        rooms_filter_desc = _describe_room_filter(resolved_rooms, resolved_room_types)
        return Command(
            update={**base_update,
                "messages": [
                    ToolMessage(
                        content=f"No rooms available for {duration_nights} "
                                f"nights for {rooms_filter_desc} "
                                f"between {start_date} and {end_date}. "
                                f"Ask user if they want to try different dates or different rooms/room types.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
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
            update={**base_update,
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
            search_result = await search_rooms(effective_start, effective_end, duration_nights)
        else:
            effective_start = start_date
            effective_end = end_date
        expanded_note = f" (window expanded by ±{expansion} days)" if expansion > 0 else ""

        # Step 1: Rooms found for full duration — return them
        if search_result.rooms:
            pending_ui_item, search_result.label = _build_pending_ui(search_result.rooms, effective_start, effective_end, search_result.criteria_id)
            return Command(
                update={**base_update,
                    "messages": [
                        ToolMessage(
                            content=f"Found {len(search_result.rooms)} room(s) for {duration_nights} "
                                    f"nights between {effective_start} and {effective_end}{expanded_note}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "pending_ui": [pending_ui_item],
                    "latest_search_results": [search_result],
                    "phase": "closing"
                }
            )

        # Step 2: No full-duration rooms — check if combinations can accommodate guest_no
        search_result_w_1_night = await search_rooms(effective_start, effective_end, 1)
        if guest_no is not None and _can_accommodate(search_result_w_1_night.rooms, guest_no):
            pending_ui_item, search_result_w_1_night.label = _build_pending_ui(search_result_w_1_night.rooms, effective_start, effective_end, search_result_w_1_night.criteria_id)
            return Command(
                update={**base_update,
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
                    "pending_ui": [pending_ui_item],
                    "latest_search_results": [search_result_w_1_night],
                    "phase": "closing"
                }
            )

        # Step 3: Not enough capacity — continue to next expansion

    # Step 4: Exhausted all expansion steps — no rooms found at all
    return Command(
        update={**base_update,
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

# ── Helpers ────────────────────────────

def _describe_room_filter(rooms: list[str] | None, types: list[str] | None) -> str:
    """Build a human-readable description from resolved room names and/or types."""
    parts = []
    if rooms:
        parts.append(', '.join(rooms))
    if types:
        parts.append(', '.join(types))
    return ' '.join(parts)

def _build_pending_ui(room_cards: list[RoomCard], start_date: str, end_date: str, criteria_id: str) -> tuple[dict, str]:
    """Build pending UI item and window label from RoomCards and date range.
    Returns (pending_ui_item, window_label).
    """
    rooms = [r.model_dump() for r in room_cards]
    label = _make_window_label(start_date, end_date)
    pending_ui_item = {
        "name": "search_window",
        "props": {"rooms": rooms, "label": label, "criteria_id": criteria_id},
        "id": str(uuid.uuid4()),
    }
    return pending_ui_item, label

def _build_date_ranges(dates: list[str], duration: int) -> list[DateRange]:
    """Find all consecutive date sequences that fit the required duration."""
    if not dates:
        return []

    sorted_dts = sorted(datetime.strptime(d, "%Y-%m-%d") for d in dates)
    ranges = []
    current_run: list[datetime] = []

    for i, dt in enumerate(sorted_dts):
        if not current_run or (dt - sorted_dts[i - 1]).days == 1:
            current_run.append(dt)
        else:
            if len(current_run) >= duration:
                ranges.append(DateRange(
                    start_date=current_run[0].strftime("%Y-%m-%d"),
                    end_date=current_run[-1].strftime("%Y-%m-%d"),
                ))
            current_run = [dt]

    if len(current_run) >= duration:
        ranges.append(DateRange(
            start_date=current_run[0].strftime("%Y-%m-%d"),
            end_date=current_run[-1].strftime("%Y-%m-%d"),
        ))

    return ranges

def _to_room_card(room: Room, date_ranges: list[DateRange]) -> RoomCard:
    """Convert a room + its date ranges into a RoomCard."""
    card = RoomCard.from_db(room)
    card.availability = RoomAvailability(
        date_ranges=date_ranges,
        nightly_rates=Rates(
            weekday=room.price_weekdays,
            weekend=room.price_weekends_holidays,
            holiday=room.price_ny_songkran,
        ),
    )
    return card

async def _attach_thumbnails(cards: list[RoomCard]) -> None:
    """Batch-fetch and attach thumbnail URLs to room cards. (I/O side effect)"""
    room_ids = [c.id for c in cards]
    if not room_ids:
        return
    thumb_map = await room_service.get_first_photo_urls(room_ids)
    for card in cards:
        card.thumbnail_url = thumb_map.get(card.id)

async def search_rooms(start_date: str, end_date: str, duration_nights: int) -> SearchResult:
    """
    Search rooms from pms with given date range.
    """
    
    availability_svc = RoomAvailabilityService()
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Fetch room availability from pms
    room_availability = await availability_svc.get_availability(start_dt, end_dt)

    # Fetch room info from our db
    db_rooms = await room_service.get_all_rooms()
    db_by_name = {r.room_name.lower(): r for r in db_rooms}

    # Filter rooms that has enough consecutive dates for the requested duration
    room_cards = []
    for room_no, room_data in room_availability.items():
        # build date ranges from available dates
        date_ranges = _build_date_ranges(room_data["dates"], duration_nights)
        db_room = db_by_name.get(room_no.lower())
        if date_ranges and db_room:
            room_cards.append(_to_room_card(db_room, date_ranges))
    
    if room_cards:
        await _attach_thumbnails(room_cards)

    return SearchResult(
        rooms=room_cards,
        expanded_days=0,
        exhausted=False,
        start_date=start_date,
        end_date=end_date,
        criteria_id=f"{start_date}-{end_date}-{duration_nights}",
        label=_make_window_label(start_date, end_date),
    )
