from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.context.agent_service_provider import AgentServiceProvider
from agent.tools.common_validators import validate_dates, validate_room_names
from agent.tools.exceptions import ToolValidationError


@tool
async def select_rooms(
    room_name: str,
    check_in_date: str,
    check_out_date: str,
    runtime: ToolRuntime[AgentServiceProvider],
) -> Command | str:
    """
    Select a room for booking. Use it when user wants to select a room
    Args:
        room_name: Room name to select. Use room names from **Available room names**
        check_in_date: Check-in date in YYYY-MM-DD format.
        check_out_date: Check-out date in YYYY-MM-DD format.

    Returns:
        Message indicating which rooms were selected.
    """

    room_availability_svc = runtime.context.room_availability
    internal_room_dict = runtime.state["rooms"]

    # Validate args
    validate_dates(check_in_date, check_out_date)
    validate_room_names(internal_room_dict, [room_name])

    # check if already selected
    if room_name in runtime.state["selected_rooms"]:
        return f"Room {room_name} is already selected. no action performed"

    is_available = await room_availability_svc.is_room_available(
        room_name, check_in_date, check_out_date
    )

    if not is_available:
        raise ToolValidationError(
            f"Room {room_name} is not available for {check_in_date} to {check_out_date}. Ask user if they want to try different dates or different rooms."
        )

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Room {room_name} selected.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "selected_rooms": {"append": [room_name]},
        }
    )
