from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from datetime import datetime

from agent.types import GlobalState
from agent.criteria_discovery.schema import Criteria
from agent.criteria_discovery.tools.booking_tools import build_scoped_booking_tools
from agent.criteria_discovery import discovery_agent


# ── Main node ──────────────────────────────────────────────────────
async def criteria_discovery_node(state: GlobalState, config: RunnableConfig):
    """
    Criteria discovery agent:
    1. Run the discovery agent with Q&A + booking process tools.
    2. If agent triggered transition → route to evaluate_options.
    """
    current_criteria = state.get("criteria") or Criteria()
    today = datetime.now().strftime("%Y-%m-%d")

    # Build booking tools with closure over current criteria and recent messages
    booking_tools, get_transition_state, get_criteria = build_scoped_booking_tools(
        current_criteria=current_criteria,
        messages=state["messages"],
        today=today,
    )

    # Run the single ReAct agent (Q&A + booking tools)
    final_msg = await discovery_agent.run(
        get_criteria=get_criteria,
        messages=state["messages"],
        today=today,
        booking_tools=booking_tools,
        config=config,
    )

    # Get updated criteria from tool closure
    criteria = get_criteria()

    # Check if ready to go to next phase
    transition_state = get_transition_state()
    if transition_state["ready"]:
        return {
            "criteria": criteria,
            "phase": "evaluate_options",
            "messages": [final_msg],
        }

    # Stay in discovery
    return {
        "criteria": criteria,
        "messages": [final_msg],
    }
