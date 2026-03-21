from typing import Annotated, Literal, Optional, Sequence, Union

from langgraph.graph import MessagesState
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer
from pydantic import BaseModel

from agent.closing.schema import ClosingState
from agent.criteria_discovery.schema import Criteria
from agent.rooms_searching.schema import RoomSearchResult

# ── Phase ──────────────────────────────────────────────────────────────────────

Phase = Literal["criteria_discovery", "room_searching", "closing"]

class GlobalState(MessagesState):
    phase: Phase
    criteria: Criteria
    criteria_ready: bool
    room_search_result: RoomSearchResult
    closing_state: ClosingState
    user_language: str
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
