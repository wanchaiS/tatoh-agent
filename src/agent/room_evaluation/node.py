from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig


from agent.types import GlobalState
from agent.shared_tools import find_boat_schedules, get_gopro_service_info, get_kohtao_arrival_guide, get_room_gallery, get_room_info
from agent.room_evaluation.schema import RoomEvaluationState
from agent.room_evaluation.room_evaluation_agent import room_evaluation_graph

qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_room_gallery,
    get_room_info,
]

tool_node = ToolNode(qa_tools, handle_tool_errors=True)
model = ChatOpenAI(model="openai/gpt-5.1-instant", temperature=0)
model_with_tools = model.bind_tools(qa_tools)

# ── Main node ──────────────────────────────────────────────────────
def room_evaluation_node(state: GlobalState, config: RunnableConfig):
    """
    Room evaluation agent, answer questions, recommend rooms and room selection
    """
    sub_config = {**(config or {}), "recursion_limit": 10}
    result = room_evaluation_graph.invoke(state, config=sub_config)

    room_evaluation_state = result.get("room_evaluation_state") or state.get("room_evaluation_state") or RoomEvaluationState()

    # if room_evaluation_state.is_ready():
    #     return Command(
    #         goto="room_searching_node",
    #         update={
    #             "criteria": criteria,
    #             "phase": "room_searching",
    #             "messages": [result["messages"][-1]],
    #         },
    #     )

    return {
        "room_evaluation_state": room_evaluation_state,
        "messages": [result["messages"][-1]],
    }