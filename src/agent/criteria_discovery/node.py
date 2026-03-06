from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

from agent.types import GlobalState
from agent.criteria_discovery.schema import Criteria
from agent.criteria_discovery.discovery_agent import criteria_discovery_graph


# ── Main node ──────────────────────────────────────────────────────
async def criteria_discovery_node(state: GlobalState, config: RunnableConfig):
    """
    Criteria discovery agent, extract criteria and answer questions
    """
    sub_config = {**(config or {}), "recursion_limit": 10}
    result = await criteria_discovery_graph.ainvoke(state, config=sub_config)

    criteria = result.get("criteria") or Criteria()
    criteria_ready = result.get("criteria_ready", False)
    criteria_confirmed = result.get("criteria_confirmed", False)

    update = {
        "criteria": criteria,
        "criteria_ready": criteria_ready,
        "criteria_confirmed": criteria_confirmed,
        "ui": result.get("ui"),
        "messages": [result["messages"][-1]],
    }

    if criteria_confirmed:
        return Command(goto="room_searching_node", update=update)

    return update
