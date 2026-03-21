import uuid

from langchain.tools import ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from agent.services.room_service import room_service
from agent.utils.tool_errors import handle_tool_error


def _model_to_dict(model):
    """Convert SQLAlchemy model to dict, excluding internal state."""
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}


@tool
@handle_tool_error
async def get_rooms_list(runtime: ToolRuntime) -> Command:
    """
    Get a list of all rooms with basic info: name, type, capacity, and pricing.
    Use this when the user asks to see all available rooms or wants an overview of room options.
    """
    rooms = await room_service.get_all_rooms()

    if not rooms:
        return Command(update={
            "pending_ui": [{
                "name": "rooms_list",
                "props": {"loading": False, "rooms": []},
                "id": str(uuid.uuid4()),
            }],
            "subgraph_messages": [ToolMessage(
                content="No rooms data available",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    room_dicts = []
    for r in rooms:
        d = _model_to_dict(r)
        d["thumbnail_url"] = await room_service.get_first_photo_url(r.id)
        room_dicts.append(d)

    prices = [r.price_weekdays for r in rooms]
    types = sorted(set(r.room_type for r in rooms))

    return Command(update={
        "pending_ui": [{
            "name": "rooms_list",
            "props": {"loading": False, "rooms": room_dicts},
            "id": str(uuid.uuid4()),
        }],
        "subgraph_messages": [ToolMessage(
            content=(
                f"Rendered {len(rooms)} rooms to the user via UI cards. "
                f"Price range: {min(prices):.0f}-{max(prices):.0f} baht/night. "
                f"Room types: {', '.join(types)}."
            ),
            tool_call_id=runtime.tool_call_id,
        )],
    })
