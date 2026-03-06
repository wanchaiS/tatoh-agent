from typing import Annotated, Literal, Optional, Union, Sequence
from pydantic import BaseModel
from langgraph.graph import MessagesState
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

from agent.criteria_discovery.schema import Criteria
from agent.room_evaluation.schema import RoomEvaluationState


# ── Phase ──────────────────────────────────────────────────────────────────────

Phase = Literal["criteria_discovery",
                  "room_searching",
                  "evaluate_options",
                  "payment_settlement",
                  "contact_info_collection",
                  "summarize_booking"]

class GlobalState(MessagesState):
    phase: Phase
    criteria: Criteria
    criteria_ready: bool
    criteria_confirmed: bool
    room_evaluation_state: RoomEvaluationState
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
