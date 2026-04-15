from agent.prompts import get_prompt_and_tools
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph.ui import push_ui_message

from agent.types import GlobalState

model = ChatOpenAI(model="openai/gpt-5.1-instant", temperature=0, streaming=True)



async def agent_node(state: GlobalState, config: RunnableConfig):
    system_prompt, tools = await get_prompt_and_tools(state)
    llm = model.bind_tools(tools)

    response = await llm.ainvoke(
        [SystemMessage(content=system_prompt)] + state["messages"],
        config,
    )

    # On final response (no tool calls): flush all pending UI cards anchored to this message
    pending = state.get("pending_ui") or []
    if not response.tool_calls and pending:
        for item in pending:
            push_ui_message(item["name"], item["props"], id=item["id"], message=response)
        return {"messages": [response], "pending_ui": []}  # [] triggers clear in reducer

    # Pre-turn reset: if this turn will call search, clear old results and signal aggregator
    update = {"messages": [response]}
    if response.tool_calls and any(
        tc["name"] == "search_available_rooms" for tc in response.tool_calls
    ):
        update["tool_room_search_results"] = []   # triggers reducer clear
        update["search_results_pending"] = True    # signal for search_result_aggregator
    return update
