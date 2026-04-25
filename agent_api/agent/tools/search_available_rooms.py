from datetime import date, datetime, timedelta
from typing import Any

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.context.agent_service_provider import AgentServiceProvider
from agent.services.room_availability_service import RoomAvailabilityService
from agent.tools.common_validators import validate_dates, validate_room_names
from agent.tools.exceptions import ToolValidationError
from agent.types import InternalRoom

EXPANSION_STEPS = [0, 3, 5, 7]

type RoomAvailabilityResult = dict[str, set[str]]


@tool
async def search_available_rooms(
    runtime: ToolRuntime[AgentServiceProvider],
    start_date: str,
    end_date: str,
    requested_rooms: list[str] | None = None,
    requested_room_types: list[str] | None = None,
) -> Command[Any] | str:
    """
    Search for available rooms based on the given criteria.

    Args:
        start_date: Start date of the search window (YYYY-MM-DD).
        end_date: End date of the search window (YYYY-MM-DD).
        requested_rooms: List of specific room numbers requested by the user. Optional.
        requested_room_types: List of room types requested by the user. Optional.
    """
    # Prepare services
    room_availability_svc = runtime.context.room_availability

    internal_room_dict: dict[str, InternalRoom] = runtime.state["rooms"]

    # Validate args
    validate_dates(start_date, end_date)

    # normalise filters so there's no need to use lowercase everywhere
    if requested_rooms:
        requested_rooms = [r.lower() for r in requested_rooms]
    if requested_room_types:
        requested_room_types = [rt.lower() for rt in requested_room_types]

    # validate filters
    validate_room_names(internal_room_dict, requested_rooms)
    _validate_room_types(internal_room_dict, requested_room_types)

    ### Searching process ###
    for expansion in EXPANSION_STEPS:
        if expansion > 0:
            today = date.today()
            expanded_start = datetime.strptime(
                start_date, "%Y-%m-%d"
            ).date() - timedelta(days=expansion)
            effective_start = max(expanded_start, today).strftime("%Y-%m-%d")
            effective_end = (
                datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=expansion)
            ).strftime("%Y-%m-%d")
        else:
            effective_start = start_date
            effective_end = end_date

        search_result = await _search_rooms(
            effective_start,
            effective_end,
            requested_rooms,
            requested_room_types,
            internal_room_dict,
            room_availability_svc,
        )

        if search_result:
            if expansion > 0:
                tool_message = f"The original date range {start_date} to {end_date} had no availability, so we expanded the search window to {effective_start} to {effective_end} and found {len(search_result)} room(s)"
            else:
                tool_message = f"Found {len(search_result)} room(s) between {effective_start} and {effective_end}"
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=tool_message,
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "pending_render_search_results": {"append": [search_result]},
                    "pending_search_range": {
                        "start": effective_start,
                        "end": effective_end,
                    },
                }
            )

    # Exhausted all expansion steps — no rooms found at all
    return f"No rooms found between {start_date} and {end_date}"


######################## Validators ################################


def _validate_room_types(
    internal_room_dict: dict[str, InternalRoom], room_types: list[str] | None = None
) -> None:
    if not room_types:
        return None

    invalid_types = []
    for room_type in room_types:
        if room_type.lower() not in [
            room["room_type"].lower() for room in internal_room_dict.values()
        ]:
            invalid_types.append(room_type)

    if invalid_types:
        valid = ", ".join(
            set(room["room_type"] for room in internal_room_dict.values())
        )
        raise ToolValidationError(
            f"Room type(s) {', '.join(invalid_types)} not found. Available room types: {valid}"
        )


######################## Helpers ################################


async def _search_rooms(
    start_date: str,
    end_date: str,
    requested_rooms: list[str] | None,
    requested_room_types: list[str] | None,
    internal_room_dict: dict[str, InternalRoom],
    availability_svc: RoomAvailabilityService,
) -> RoomAvailabilityResult:
    """Search rooms from PMS. Returns raw room names + available dates."""
    room_availability = await availability_svc.get_availability(start_date, end_date)

    # Filter rooms that exist internally and match requested rooms/room types
    qualified_rooms: RoomAvailabilityResult = {}
    for room_no, room_data in room_availability.items():
        if not room_data["dates"]:
            continue

        room_no_lower = room_no.lower()
        room_type_lower = room_data["room_type_name"].lower()

        # room dont exist in the system
        if room_no_lower not in internal_room_dict:
            continue

        # room is requested but not available
        if requested_rooms and room_no_lower not in requested_rooms:
            continue
        if requested_room_types and room_type_lower not in requested_room_types:
            continue

        # add room to qualified rooms
        qualified_rooms[room_no_lower] = room_data["dates"]

    return qualified_rooms
