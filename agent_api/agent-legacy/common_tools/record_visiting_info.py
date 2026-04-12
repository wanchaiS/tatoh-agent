from typing import Optional

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from pydantic import BaseModel


class VisitingInfo(BaseModel):
    """Guest's visiting facts passively collected from the conversation."""

    guest_count: Optional[int] = None
    duration_nights: Optional[int] = None
    guest_arrival_date: Optional[str] = None
    guest_departure_date: Optional[str] = None


@tool
async def record_visiting_info(
    guest_count: Optional[int] = None,
    duration_nights: Optional[int] = None,
    guest_arrival_date: Optional[str] = None,
    guest_departure_date: Optional[str] = None,
    runtime: ToolRuntime = None,
) -> Command:
    """Record visiting facts inferred from the conversation. Call this silently whenever
    the user mentions dates, guest count, or duration — do NOT acknowledge this tool call to the user.
    Only pass fields you are confident about. Partial updates are fine.

    Args:
        guest_count: Total number of guests (adults + children).
        duration_nights: Number of nights for the stay.
        guest_arrival_date: Guest arrival date at the resort in YYYY-MM-DD format.  
        guest_departure_date: Guest departure date from the resort in YYYY-MM-DD format.
    """
    current: VisitingInfo = runtime.state.get("visiting_info") or VisitingInfo()

    updates = {}
    if guest_count is not None:
        updates["guest_count"] = guest_count
    if duration_nights is not None:
        updates["duration_nights"] = duration_nights
    if guest_arrival_date is not None:
        updates["guest_arrival_date"] = guest_arrival_date
    if guest_departure_date is not None:
        updates["guest_departure_date"] = guest_departure_date

    if not updates:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No visiting info fields provided.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    updated_visiting_info = current.model_copy(update=updates)
    return Command(
        update={
            "visiting_info": updated_visiting_info,
            "messages": [
                ToolMessage(
                    content=f"Visiting info updated: {updates}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
