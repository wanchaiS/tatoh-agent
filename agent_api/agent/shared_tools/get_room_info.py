from dataclasses import asdict

from langchain.tools import tool
from langgraph.graph.ui import push_ui_message

from agent.services.room_service import room_service
from agent.utils.tool_errors import handle_tool_error


@tool
@handle_tool_error
def get_room_info(room_number: str) -> str:
    """
    Get room information for a specific room number.

    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """

    room = room_service.get_room_by_name(room_number)

    if room:
        # Emit room detail UI card directly from the tool
        push_ui_message("room_detail", {"room": asdict(room)})

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
