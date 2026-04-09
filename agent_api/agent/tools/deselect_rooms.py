from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from agent.context.agent_service_provider import AgentServiceProvider
from agent.tools.common_validators import validate_room_names

@tool
async def deselect_rooms(room_name: str,
                        runtime: ToolRuntime[AgentServiceProvider]):
    """
    Deselect a room for booking. Use it when user wants to deselect a room
    Args:
        room_name: Room name to deselect. Use room names from **Available room names**
    
    Returns:
        Message indicating which rooms were deselected.
    """
    
    internal_room_dict = runtime.state["rooms"]

    # Validate args
    validate_room_names(internal_room_dict, [room_name])

    # check if already selected
    if room_name not in runtime.state["selected_rooms"]:
        return f"Room {room_name} is not selected. no action performed"

    return Command(update={
        "messages": [ToolMessage(
            content=f"Room {room_name} deselected.",
            tool_call_id=runtime.tool_call_id,
        )],
        "selected_rooms": {"remove": room_name},
    })