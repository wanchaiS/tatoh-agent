from typing import Optional

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.schemas import UserPreferences


@tool
async def record_preference(
    location_preference: Optional[str] = None,
    privacy_preferred: Optional[bool] = None,
    group_type: Optional[str] = None,
    mobility_limited: Optional[bool] = None,
    runtime: ToolRuntime = None,
) -> Command:
    """Record soft user preferences inferred from the conversation. Call this silently whenever
    you clearly infer a preference — do NOT acknowledge this tool call to the user.
    Only pass fields you are confident about. Partial updates are fine.

    Args:
        location_preference: Where on the resort hill the guest prefers to stay.
            The resort is built on a slope — rooms lower on the hill are closer to the beach
            (better sea view, longer walk up to facilities). Rooms higher up are closer to the
            restaurant, reception, and main road (less walking, but farther from beach/view).
            'beach_side' = they prioritise beach access or sea view.
            'facilities_side' = they prefer easy access to restaurant/reception/main road.
            'middle' = they want a balance of both.
        privacy_preferred: True if the guest wants seclusion or a quiet, private spot
            (e.g. honeymoon, 'somewhere secluded', 'away from other guests').
        group_type: Type of travelling group.
            'couple' = two adults, especially romantic/honeymoon trips.
            'family' = children or parents travelling together.
            'friends' = group of adults, non-romantic context.
            'solo' = single traveller.
        mobility_limited: True if any guest may struggle with slopes or long walks —
            includes elderly guests, guests with physical conditions (bad knee, back problems),
            or guests with a baby stroller. Strongly affects location recommendations.
    """
    current: UserPreferences = runtime.state.get("preferences") or UserPreferences()

    updates = {}
    if location_preference is not None:
        valid = {"beach_side", "middle", "facilities_side"}
        if location_preference not in valid:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Invalid location_preference '{location_preference}'. Must be one of: {valid}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ]
                }
            )
        updates["location_preference"] = location_preference
    if privacy_preferred is not None:
        updates["privacy_preferred"] = privacy_preferred
    if group_type is not None:
        valid_groups = {"couple", "family", "friends", "solo"}
        if group_type not in valid_groups:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Invalid group_type '{group_type}'. Must be one of: {valid_groups}.",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ]
                }
            )
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
