import uuid

from agent.services.room_schemas import RoomCard
from agent.utils.tool_errors import handle_tool_error
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from agent.services.room_service import room_service


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
            "pending_ui": [{"name": "rooms_list", "props": {"loading": False, "rooms": []}, "id": str(uuid.uuid4())}],
            "messages": [ToolMessage(
                content="No rooms data available",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    room_ids = [r.id for r in rooms]
    thumb_map = await room_service.get_first_photo_urls(room_ids)
    cards = [RoomCard.from_db(r, thumbnail_url=thumb_map.get(r.id)) for r in rooms]

    prices = [c.price_weekdays for c in cards]
    types = sorted(set(c.room_type for c in cards))

    push_ui_item = {"name": "rooms_list", "props": {"loading": False, "rooms": [c.model_dump() for c in cards]}, "id": str(uuid.uuid4())}
    return Command(update={
        "pending_ui": [push_ui_item],
        "messages": [ToolMessage(
            content=(
                f"Rendered {len(cards)} rooms to the user via UI cards. "
                f"Price range: {min(prices):.0f}-{max(prices):.0f} baht/night. "
                f"Room types: {', '.join(types)}."
            ),
            tool_call_id=runtime.tool_call_id,
        )],
    })
