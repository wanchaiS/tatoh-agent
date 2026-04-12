from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.services.room_cache import room_cache
from agent.closing_phase.schemas import ClosingState, RoomSelection


@tool
async def deselect_room(
    room_name: str,
    runtime: ToolRuntime = None,
) -> Command:
    """Remove a room from the current selection.

    Args:
        room_name: Room number to remove (e.g. "s5").
    """

    if not room_name:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="Error: room_name is required.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    selected_rooms: list[RoomSelection] = runtime.state.get("selected_rooms") or []

    if not selected_rooms:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="Cannot deselect a room. No rooms have been selected.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    # Find and remove
    remaining = [
        r for r in selected_rooms
        if r.room_name.lower() != room_name.lower()
    ]

    if len(remaining) == len(selected_rooms):
        selected = ", ".join(r.room_name for r in selected_rooms)
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=(
                            f"Room '{room_name}' is not in the current selection. "
                            f"Currently selected: {selected or 'none'}. "
                            f"Available rooms: {await room_cache.get_room_names_str()}"
                        ),
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    return Command(
        update={
            "selected_rooms": remaining,
            "messages": [
                ToolMessage(
                    content=f"Room '{room_name}' has been deselected.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
