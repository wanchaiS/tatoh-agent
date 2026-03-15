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
async def get_room_info(room_number: str) -> str:
    """
    Get room information for a specific room number.

    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """
    error_msg = await room_service.validate_room(room_number)
    if error_msg:
        return error_msg

    msg_id = str(uuid.uuid4())
    # Emit loading skeleton immediately
    push_ui_message("room_detail", {"loading": True, "room": None}, id=msg_id)

    room = await room_service.get_room_by_name(room_number)

    if room:
        # Emit real data (replaces loading state via reducer)
        room_dict = _model_to_dict(room)
        room_dict["thumbnail_url"] = await room_service.get_first_photo_url(room.id)
        push_ui_message("room_detail", {"loading": False, "room": room_dict}, id=msg_id)

        return (
            f"Rendered room detail card for {room.room_name} ({room.room_type}) to the user via UI. "
            f"Room summary: {room.summary}. "
            f"Weekday price: {room.price_weekdays:.0f} baht/night."
            f"Weekends price: {room.price_weekends_holidays:.0f} baht/night."
            f"New Year and Songkran price: {room.price_ny_songkran:.0f} baht/night."
            f"Max guests: {room.max_guests}. "
        )
    else:
        return f"ไม่พบข้อมูลห้องพัก {room_number} กรุณาระบุหมายเลขห้องพักให้ถูกต้อง เช่น S1, V2"
