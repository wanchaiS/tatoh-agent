from dataclasses import asdict

from langchain.tools import tool
from langgraph.graph.ui import push_ui_message

from agent.services.room_service import room_service
from agent.utils.tool_errors import handle_tool_error


@tool
@handle_tool_error
def get_rooms_list() -> str:
    """
    Get a list of all rooms with basic info: name, type, capacity, and pricing.
    Use this when the user asks to see all available rooms or wants an overview of room options.
    """
    # Emit loading skeleton immediately
    push_ui_message("rooms_list", {"loading": True, "rooms": []})

    rooms = room_service.get_all_rooms()

    if not rooms:
        push_ui_message("rooms_list", {"loading": False, "rooms": []})
        return "No rooms data available"

    # Emit real data (replaces loading state via reducer)
    push_ui_message("rooms_list", {"loading": False, "rooms": [asdict(r) for r in rooms]})

    prices = [r.price_weekdays for r in rooms]
    types = sorted(set(r.room_type for r in rooms))

    return (
        f"Rendered {len(rooms)} rooms to the user via UI cards. "
        f"Price range: {min(prices):.0f}-{max(prices):.0f} baht/night. "
        f"Room types: {', '.join(types)}."
    )
