from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command


@tool
async def update_guest_count(
    total_guests: int,
    runtime: ToolRuntime = None,
) -> Command:
    """Update the total number of guests for the booking. Use this in the closing phase
    when the guest count needs to be set or changed without re-searching for rooms.

    Args:
        total_guests: Total number of guests including children.
    """
    if total_guests < 1:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="Guest count must be at least 1.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    updated_criteria = current_criteria.model_copy(update={"total_guests": total_guests})

    parts = [f"Guest count updated to {total_guests}."]

    # If rooms are already selected, provide capacity context
    closing_state = runtime.state.get("closing_state")
    if closing_state and closing_state.selected_rooms:
        search_result = runtime.state.get("room_search_result")
        if search_result:
            total_capacity = 0
            for sel in closing_state.selected_rooms:
                for sr in search_result.rooms:
                    if sr.room_name.lower() == sel.room_name.lower():
                        total_capacity += sr.max_guests
                        break
            max_with_beds = total_capacity + len(closing_state.selected_rooms)
            parts.append(
                f"Current selection: {len(closing_state.selected_rooms)} room(s), "
                f"base capacity {total_capacity}, max with extra beds {max_with_beds}."
            )
            if total_guests > max_with_beds:
                parts.append(
                    f"WARNING: {total_guests} guests exceed maximum capacity ({max_with_beds}). "
                    f"Additional rooms needed or guest count must be reduced."
                )
            elif total_guests > total_capacity:
                parts.append(
                    f"Note: {total_guests} guests exceed base capacity ({total_capacity}). "
                    f"Extra beds will be needed."
                )

    return Command(
        update={
            "criteria": updated_criteria,
            "messages": [
                ToolMessage(
                    content="\n".join(parts),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
