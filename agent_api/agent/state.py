from typing import Annotated, Dict, Sequence, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

from agent.tools.search_available_rooms import RoomAvailabilityResult
from agent.types import InternalRoom


def list_reducer(existing: list[str], update: dict) -> list[str]:
    """Custom reducer for list[str]: supports append, clear, remove."""
    if "clear" in update:
        return []

    if existing is None:
        existing = []

    if "append" in update:
        existing.extend(update["append"])
        return existing

    if "remove" in update:
        to_remove = update["remove"]
        return [x for x in existing if x != to_remove]

    return existing


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pending_render_search_results: Annotated[list[RoomAvailabilityResult], list_reducer]
    pending_search_range: dict[str, str] | None  # {"start": ..., "end": ...}
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    rooms: Dict[str, InternalRoom]  # no reducer, always replace
