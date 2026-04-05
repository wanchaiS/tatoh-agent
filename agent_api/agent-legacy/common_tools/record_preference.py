from typing import Literal, Optional

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from pydantic import BaseModel

LocationPreference = Literal["beach_side", "middle", "facilities_side"]
GroupType = Literal["couple", "family", "friends", "solo"]


class UserPreferences(BaseModel):
    """Soft preferences passively collected from the conversation."""

    location_preference: Optional[LocationPreference] = None
    privacy_preferred: Optional[bool] = None
    group_type: Optional[GroupType] = None
    mobility_limited: Optional[bool] = None


@tool
async def record_preference(
    location_preference: Optional[LocationPreference] = None,
    privacy_preferred: Optional[bool] = None,
    group_type: Optional[GroupType] = None,
    mobility_limited: Optional[bool] = None,
    runtime: ToolRuntime = None,
) -> Command:
    """Record soft user preferences inferred from the conversation. Call this silently whenever
    you clearly infer a preference — do NOT acknowledge this tool call to the user.
    Only pass fields you are confident about. Partial updates are fine.

    Args:
        location_preference: Preferred position on the resort hill.
            The resort is on a slope — lower = closer to beach/sea view, upper = closer to facilities.
            beach_side: prioritises beach access or sea view.
            facilities_side: prefers easy access to restaurant, reception, main road.
            middle: balance of both.
        privacy_preferred: True if the guest wants seclusion or a quiet, private spot
            (e.g. honeymoon, 'somewhere secluded', 'away from other guests').
        group_type: Type of travelling group.
            couple: two adults, romantic/honeymoon.
            family: children or parents travelling together.
            friends: group of adults, non-romantic.
            solo: single traveller.
        mobility_limited: True if any guest may struggle with slopes or long walks —
            includes elderly guests, guests with physical conditions (bad knee, back problems),
            or guests with a baby stroller. Strongly affects location recommendations.
    """
    current: UserPreferences = runtime.state.get("preferences") or UserPreferences()

    updates = {}
    if location_preference is not None:
        updates["location_preference"] = location_preference
    if privacy_preferred is not None:
        updates["privacy_preferred"] = privacy_preferred
    if group_type is not None:
        updates["group_type"] = group_type
    if mobility_limited is not None:
        updates["mobility_limited"] = mobility_limited

    if not updates:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No preference fields provided.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    updated_preferences = current.model_copy(update=updates)
    return Command(
        update={
            "preferences": updated_preferences,
            "messages": [
                ToolMessage(
                    content=f"Preferences updated: {updates}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
