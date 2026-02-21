from langgraph.types import Command
from datetime import datetime

from agent.types import GlobalState
from agent.criteria_discovery.schema import Criteria
from agent.criteria_discovery.tools import build_booking_tools
from agent.criteria_discovery import discovery_agent


# ── Main node ──────────────────────────────────────────────────────
def criteria_discovery_node(state: GlobalState):
    """
    Single-agent discovery node:
    1. Build procedural tools (extraction + transition) with closure over current state.
    2. Run the discovery agent with Q&A + procedural tools.
    3. If agent triggered transition → route to evaluate_options.
    """
    current_criteria = state.get("criteria_discovery_state") or Criteria()
    today = datetime.now().strftime("%Y-%m-%d")

    # Build booking tools with closure over current criteria and recent messages
    booking_tools, is_transition_ready, get_criteria = build_booking_tools(
        current_criteria=current_criteria,
        messages=state["messages"],
        today=today,
    )

    # Run the single ReAct agent (Q&A + procedural tools)
    final_msg = discovery_agent.run(
        criteria=current_criteria,
        messages=state["messages"],
        today=today,
        booking_tools=booking_tools,
    )

    # Get updated criteria from tool closure
    criteria = get_criteria()

    # Check if agent signaled transition via proceed_to_room_search tool
    if is_transition_ready():
        return Command(
            update={
                "criteria_discovery_state": criteria,
                "phase": "evaluate_options",
                "messages": [final_msg],
            },
            goto="evaluate_options_node",
        )

    # Stay in discovery
    return {
        "criteria_discovery_state": criteria,
        "messages": [final_msg],
    }
