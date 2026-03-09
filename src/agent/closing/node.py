from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from agent.types import GlobalState
from agent.closing.schema import ClosingState


async def closing_node(state: GlobalState, config: RunnableConfig):
    """
    Closing phase node — guides user from room selection to booking.
    Currently a stub that echoes back to the user.
    """
    closing = state.get("closing_state") or ClosingState()

    return {
        "closing_state": closing,
        "messages": [AIMessage(content="[Closing phase not yet implemented]")],
    }
