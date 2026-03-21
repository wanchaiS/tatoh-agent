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
async def get_room_info(room_number: str, runtime: ToolRuntime) -> Command:
    """
    Get room information for a specific room number.

    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """
    error_msg = await room_service.validate_room(room_number)
    if error_msg:
        return Command(update={
            "subgraph_messages": [ToolMessage(
                content=error_msg,
                tool_call_id=runtime.tool_call_id,
            )],
        })

    room = await room_service.get_room_by_name(room_number)

    if room:
        room_dict = _model_to_dict(room)
        room_dict["thumbnail_url"] = await room_service.get_first_photo_url(room.id)

        return Command(update={
            "pending_ui": [{
                "name": "room_detail",
                "props": {"loading": False, "room": room_dict},
                "id": str(uuid.uuid4()),
            }],
            "subgraph_messages": [ToolMessage(
                content=(
                    f"Rendered room detail card for {room.room_name} ({room.room_type}) to the user via UI. "
                    f"Room summary: {room.summary}. "
                    f"Weekday price: {room.price_weekdays:.0f} baht/night."
                    f"Weekends price: {room.price_weekends_holidays:.0f} baht/night."
                    f"New Year and Songkran price: {room.price_ny_songkran:.0f} baht/night."
                    f"Max guests: {room.max_guests}. "
                ),
                tool_call_id=runtime.tool_call_id,
            )],
        })
    else:
        return Command(update={
            "subgraph_messages": [ToolMessage(
                content=f"ไม่พบข้อมูลห้องพัก {room_number} กรุณาระบุหมายเลขห้องพักให้ถูกต้อง เช่น S1, V2",
                tool_call_id=runtime.tool_call_id,
            )],
        })
