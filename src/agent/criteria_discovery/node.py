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

    criteria = result.get("criteria") or state.get("criteria") or Criteria()

    if criteria.is_ready():
        return Command(
            goto="room_searching_node",
            update={
                "criteria": criteria,
                "phase": "room_searching",
                "messages": [result["messages"][-1]],
            },
        )

    return {
        "criteria": criteria,
        "messages": [result["messages"][-1]],
    }
