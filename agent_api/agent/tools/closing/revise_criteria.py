from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.schemas import ClosingState


@tool
def revise_criteria(runtime: ToolRuntime = None):
    """
    Route to criteria discovery node when user wants to revise their criteria.
    """
    return Command(
        update={
            "phase": "criteria_discovery",
            "criteria_ready": False,
            "closing_state": ClosingState(),
            "latest_search_results": [],
            "messages": [
                ToolMessage(
                    content="Transitioned back to criteria discovery. User wants to change criteria.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
