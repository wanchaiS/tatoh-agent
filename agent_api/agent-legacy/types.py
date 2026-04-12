from typing import Annotated, List, Literal, Sequence
from typing_extensions import TypedDict

from langgraph.graph import MessagesState
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

from agent.services.room_schemas import RoomCard
from agent.closing_phase.schemas import ClosingState, RoomSelection
from agent.search_phase.tools.search_available_rooms import ToolRoomSearchResult
from agent.common_tools.record_visiting_info import VisitingInfo
from agent.common_tools.record_preference import UserPreferences


class PendingUIItem(TypedDict):
    name: str
    props: dict
    id: str


def _pending_ui_reducer(current: list | None, update: list) -> list:
    """Reducer for pending_ui staging list.
    - Empty list update [] = clear signal (agent just flushed)
    - Non-empty update = append new items, deduplicating by id
    """
    if not update:
        return []
    current = current or []
    existing_ids = {item["id"] for item in current}
    return current + [item for item in update if item["id"] not in existing_ids]


def _search_results_reducer(current: list | None, update: list) -> list:
    """Reducer for tool_room_search_results.
    - Empty list [] = clear
    - Non-empty = append new results
    """
    if not update:
        return []
    return (current or []) + update

def _room_selection_reducer(current: list | None, update: list) -> list:
    """Reducer for selected_rooms.
    - Empty list [] = clear
    - Non-empty = append new room selection
    """
    if not update:
        return []
    return (current or []) + update
    

Phase = Literal["criteria_discovery", "closing"]
DEFAULT_PHASE: Phase = "criteria_discovery"

class GlobalState(MessagesState):
    phase: Phase = DEFAULT_PHASE
    tool_room_search_results: Annotated[List[ToolRoomSearchResult], _search_results_reducer]
    aggregated_room_search_results: List[RoomCard]
    selected_rooms: Annotated[List[RoomSelection], _room_selection_reducer]
    visiting_info: VisitingInfo
    user_language: str
    preferences: UserPreferences
    search_results_pending: bool
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    pending_ui: Annotated[List[PendingUIItem], _pending_ui_reducer]
