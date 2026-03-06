from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain.tools import ToolRuntime
from langgraph.types import Command


@tool
def confirm_search(runtime: ToolRuntime = None) -> Command:
    """Confirm that the user has reviewed and approved the booking criteria summary.
    Call this tool ONLY after presenting the full criteria summary to the user
    and receiving their explicit confirmation to proceed with the room search.
    Do NOT call this speculatively — wait for the user to say yes.
    """
    criteria_ready = runtime.state.get("criteria_ready") or False

    if not criteria_ready:
        return Command(update={
            "messages": [ToolMessage(
                content="Cannot confirm: criteria are not fully filled and validated yet. "
                        "Complete all required fields via update_criteria first.",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    return Command(update={
        "criteria_confirmed": True,
        "messages": [ToolMessage(
            content="Confirmed. Proceeding to room search.",
            tool_call_id=runtime.tool_call_id,
        )],
    })
