"""Remove stale UI messages (e.g. suggested_answers) at the start of each turn."""

from langgraph.graph.ui import delete_ui_message

from agent.types import GlobalState


def ui_cleanup_node(state: GlobalState) -> dict:
    """Delete transient UI messages so they don't persist across turns."""
    for msg in state.get("ui", []):
        if msg.get("name") == "suggested_answers":
            delete_ui_message(msg["id"])
    return {}
