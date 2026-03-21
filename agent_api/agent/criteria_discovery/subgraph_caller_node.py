from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.ui import push_ui_message

from agent.criteria_discovery.discovery_graph import criteria_discovery_graph
from agent.criteria_discovery.schema import Criteria
from agent.types import GlobalState


async def subgraph_caller_node(state: GlobalState, config: RunnableConfig):

    sub_config = {**(config or {}), "recursion_limit": 10}
    subgraph_input = {
        "criteria": state.get("criteria") or Criteria(),
        "subgraph_messages": state.get("messages", []),
        "is_criteria_ready": state.get("is_criteria_ready", False),
        "pending_ui": [],
    }

    result = await criteria_discovery_graph.ainvoke(subgraph_input, config=sub_config)

    criteria = result.get("criteria") or Criteria()
    criteria_ready = result.get("is_criteria_ready", False)
    phase = "room_searching" if criteria_ready else "criteria_discovery"

    last_msg = result["subgraph_messages"][-1]

    # Push all pending UI cards anchored to the final AI message
    for ui_item in result.get("pending_ui", []):
        push_ui_message(
            ui_item["name"],
            ui_item["props"],
            id=ui_item["id"],
            message=AIMessage(id=last_msg.id, content=""),
        )

    return {
        "criteria": criteria,
        "criteria_ready": criteria_ready,
        "messages": [last_msg],
        "phase": phase,
    }
