from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command


@tool
def revise_criteria(runtime: ToolRuntime = None):
    """
    User wants to search again, transit to criteria discovery phase.
    """
    return Command(
        update={
            "phase": "criteria_discovery",
            "messages": [
                ToolMessage(
                    content="Transitioned back to criteria discovery phase. User wants to search again.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
