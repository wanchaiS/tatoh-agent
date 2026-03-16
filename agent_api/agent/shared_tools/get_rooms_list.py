import uuid
from typing import Annotated

from langchain.tools import tool
from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message
from langgraph.prebuilt import InjectedState

from agent.services.room_service import room_service
from agent.utils.tool_errors import handle_tool_error


def _model_to_dict(model):
    """Convert SQLAlchemy model to dict, excluding internal state."""
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}


@tool
@handle_tool_error
async def get_rooms_list(state: Annotated[dict, InjectedState]) -> str:
    """
    Get a list of all rooms with basic info: name, type, capacity, and pricing.
    Use this when the user asks to see all available rooms or wants an overview of room options.
    """
    # bind anchor id to the last message so it can render with "messages" in the UI
    anchor_id = state.get("ui_anchor_id")
    anchor_msg = AIMessage(id=anchor_id, content="")

    msg_id = str(uuid.uuid4())
    # Emit loading skeleton immediately
    push_ui_message("rooms_list", {"loading": True, "rooms": []}, id=msg_id, message=anchor_msg)

    rooms = await room_service.get_all_rooms()

    if not rooms:
        push_ui_message("rooms_list", {"loading": False, "rooms": []}, id=msg_id, message=anchor_msg)
        return "No rooms data available"

    # Emit real data (replaces loading state via reducer)
    room_dicts = []
    for r in rooms:
        d = _model_to_dict(r)
        d["thumbnail_url"] = await room_service.get_first_photo_url(r.id)
        room_dicts.append(d)
    push_ui_message("rooms_list", {"loading": False, "rooms": room_dicts}, id=msg_id, message=anchor_msg)

    prices = [r.price_weekdays for r in rooms]
    types = sorted(set(r.room_type for r in rooms))

    return (
        f"Rendered {len(rooms)} rooms to the user via UI cards. "
        f"Price range: {min(prices):.0f}-{max(prices):.0f} baht/night. "
        f"Room types: {', '.join(types)}."
    )
