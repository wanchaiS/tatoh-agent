from datetime import datetime

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.pricing import calculate_stay_pricing
from agent.services.room_schemas import RoomCard
from agent.closing_phase.schemas import RoomSelection


def _find_room(room_name: str, room_cards: list[RoomCard]) -> RoomCard | None:
    """Find a room by exact name (case-insensitive) in aggregated results."""
    for r in room_cards:
        if r.room_name.lower() == room_name.lower():
            return r
    return None


def _is_available(room: RoomCard, check_in: str, check_out: str) -> bool:
    """Check if the requested stay fits within any available date range."""
    if not room.availability:
        return False
    for dr in room.availability.date_ranges:
        if check_in >= dr.start_date and check_out <= dr.end_date:
            return True
    return False


def _format_available_ranges(room: RoomCard) -> str:
    """Format available date ranges for error messages."""
    return ", ".join(
        f"{dr.start_date} to {dr.end_date}" for dr in room.availability.date_ranges
    )

def _error(msg: str, tool_call_id: str) -> Command:
    return Command(
        update={"messages": [ToolMessage(content=f"Error: {msg}", tool_call_id=tool_call_id)]}
    )


@tool
async def select_room(
    room_name: str,
    check_in: str,
    check_out: str,
    staying_guests: int,
    extra_bed: bool = False,
    runtime: ToolRuntime = None,
) -> Command:
    """Select a room and lock in check-in/check-out dates. Call once per room.
    If the same room is already selected, it will be replaced with the new dates/settings.

    Args:
        room_name: Room name from the search results (e.g. "s5", "v2").
        check_in: Check-in date in YYYY-MM-DD format.
        check_out: Check-out date in YYYY-MM-DD format.
        extra_bed: Set to true to add an extra bed to this room (500 THB/night). Only set when user explicitly requests it or when instructed by a previous tool response.
        staying_guests: Number of guests staying in this room.
    """

    # Validate if room exist
    if not room_name:
        return _error("Room name is required. Ask user for the room name.", runtime.tool_call_id)

    # Check if selected room exist in the result
    room_cards: list[RoomCard] = runtime.state.get("aggregated_room_search_results", [])
    if not room_cards:
        return _error("No search results available for room selection. Some unexpected error occurred, ask user to search again.", runtime.tool_call_id)

    # validate checkin,out
    # args take priority over state, we sync state after successful room selection
    booking_info = runtime.state.get("booking_info",{})
    effective_check_in = check_in or booking_info.get("check_in_date")
    effective_check_out = check_out or booking_info.get("check_out_date")

    if not effective_check_in or not effective_check_out:
        return _error("Check-in and check-out dates are required. Ask user for the check-in and check-out dates.", runtime.tool_call_id)

    if effective_check_out <= effective_check_in:
        return _error("Check-out date must be after check-in date. Ask user for the correct dates.", runtime.tool_call_id)

    room = _find_room(room_name, room_cards)

    if not room:
        return _error(f"Room '{room_name}' not found in search results. Ask user to select a room from the search results.", runtime.tool_call_id)
    
    if not _is_available(room, effective_check_in, effective_check_out):
        return _error(f"Room '{room_name}' is not available for {effective_check_in} to {effective_check_out}. The room is only available on {_format_available_ranges(room)}. Ask user to select another room or different dates.", runtime.tool_call_id)
    
    # validate staying guests vs max guests
    if staying_guests > room.max_guests and not extra_bed:
        if staying_guests > room.max_guests + 1:
            return _error(f"Room '{room_name}' can accommodate {room.max_guests + 1} guests included one extra bed. You are trying to accommodate {staying_guests} guests. one bed extension is maximum", runtime.tool_call_id)
        else:
            return _error(f"Room '{room_name}' can accommodate {room.max_guests} guests. You are trying to accommodate {staying_guests} guests. Ask user if they want one extension bed.", runtime.tool_call_id)
    
    # all good we can select this room
    # calculate the price for this room
    pricing = calculate_stay_pricing(effective_check_in, effective_check_out, room.rates, extra_bed)

    return Command(
        update={
            "selected_rooms": [RoomSelection(
                room_name=room.room_name,
                check_in=effective_check_in,
                check_out=effective_check_out,
                extra_bed=extra_bed,
                pricing=pricing,
            )],
            "messages": [
                ToolMessage(
                    content=f"Room '{room_name}' has been selected for {effective_check_in} to {effective_check_out}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
