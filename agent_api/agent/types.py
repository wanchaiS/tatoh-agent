from typing import Annotated, List, Literal, Optional, Sequence, Union

from langgraph.graph import MessagesState
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer
from pydantic import BaseModel

from agent.schemas import ClosingState, Criteria, PendingUIItem, RoomSearchResult, UserPreferences
from agent.tools.discovery_criteria.search_available_rooms import SearchResult


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
    """Reducer for latest_search_results.
    - Empty list [] = clear (pre-turn reset)
    - Non-empty = append new results
    """
    if not update:
        return []
    return (current or []) + update

# ── Phase ──────────────────────────────────────────────────────────────────────

Phase = Literal["criteria_discovery", "closing"]

class GlobalState(MessagesState):
    phase: Phase = "criteria_discovery"
    criteria: Criteria
    criteria_ready: bool
    room_search_result: RoomSearchResult
    latest_search_results: Annotated[List[SearchResult], _search_results_reducer]
    closing_state: ClosingState
    user_language: str
    preferences: UserPreferences
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    pending_ui: Annotated[List[PendingUIItem], _pending_ui_reducer]
