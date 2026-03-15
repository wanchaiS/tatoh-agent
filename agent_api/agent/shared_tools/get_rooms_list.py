import uuid

from langchain.tools import tool
from langgraph.graph.ui import push_ui_message

from agent.services.room_service import room_service
from agent.utils.tool_errors import handle_tool_error


def _model_to_dict(model):
    """Convert SQLAlchemy model to dict, excluding internal state."""
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}


@tool
@handle_tool_error
async def get_rooms_list() -> str:
    """
    Get a list of all rooms with basic info: name, type, capacity, and pricing.
    Use this when the user asks to see all available rooms or wants an overview of room options.
    """
    msg_id = str(uuid.uuid4())
    # Emit loading skeleton immediately
    push_ui_message("rooms_list", {"loading": True, "rooms": []}, id=msg_id)

    rooms = await room_service.get_all_rooms()

    if not rooms:
        push_ui_message("rooms_list", {"loading": False, "rooms": []}, id=msg_id)
        return "No rooms data available"

    # Emit real data (replaces loading state via reducer)
    room_dicts = []
    for r in rooms:
        d = _model_to_dict(r)
        d["thumbnail_url"] = await room_service.get_first_photo_url(r.id)
        room_dicts.append(d)
    push_ui_message("rooms_list", {"loading": False, "rooms": room_dicts}, id=msg_id)

    prices = [r.price_weekdays for r in rooms]
    types = sorted(set(r.room_type for r in rooms))

    return (
        f"Rendered {len(rooms)} rooms to the user via UI cards. "
        f"Price range: {min(prices):.0f}-{max(prices):.0f} baht/night. "
        f"Room types: {', '.join(types)}."
    )
