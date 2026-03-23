from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.schemas import ClosingState


@tool
async def deselect_room(
    room_name: str,
    runtime: ToolRuntime = None,
) -> Command:
    """Remove a room from the current selection.

    Args:
        room_name: Room number to remove (e.g. "s5").
    """
    closing_state: ClosingState = runtime.state.get("closing_state") or ClosingState()

    # Find and remove
    remaining = [
        r for r in closing_state.selected_rooms
        if r.room_name.lower() != room_name.lower()
    ]

    if len(remaining) == len(closing_state.selected_rooms):
        selected = ", ".join(r.room_name for r in closing_state.selected_rooms)
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=(
                            f"Room '{room_name}' is not in the current selection. "
                            f"Currently selected: {selected or 'none'}"
                        ),
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    updated_state = ClosingState(
        selected_rooms=remaining,
        terms_and_payment_shown=False,  # Reset — selection changed
    )

    parts = [f"Room {room_name} removed from selection."]
    if remaining:
        total = sum(r.pricing.total_price for r in remaining)
        for r in remaining:
            bed = " (+extra bed)" if r.extra_bed else ""
            parts.append(f"- {r.room_name}{bed}: {r.pricing.total_price:,.0f} THB")
        parts.append(f"Remaining total: {total:,.0f} THB")
    else:
        parts.append("No rooms selected.")

    return Command(
        update={
            "closing_state": updated_state,
            "messages": [
                ToolMessage(
                    content="\n".join(parts),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
