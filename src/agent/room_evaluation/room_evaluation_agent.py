from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from typing import List
import json

from agent.room_evaluation.schema import RoomEvaluationState
from agent.criteria_discovery.schema import Criteria
from agent.shared_tools import (
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
    no_tool_found,
    out_of_scope,
)

# ── Shared Q&A tools (always available) ──────────────────────────
qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
    no_tool_found,
    out_of_scope,
]


def build_system_prompt(room_evaluation_state: RoomEvaluationState, today: str) -> str:
    guest_meta_data = room_evaluation_state.guest_meta_data or "Not yet provided"
    selected_room_no = room_evaluation_state.selected_room_no or "Not yet selected"
    
    return f"""You are Cooper (คูเปอร์), the expert Room Consultant for Tatoh Resort. 
Address the user kindly as "คุณลูกค้า".

[CONTEXT]
Today's Date: {today}
Guest Metadata: {guest_meta_data}
Currently Selected Room No: {selected_room_no}

[AVAILABLE ROOMS (TRUTH)]
You may ONLY recommend or discuss the rooms listed below. Do not hallucinate availability.
{room_evaluation_state.current_search_results} 

[CORE DIRECTIVE: CONSULT & CLOSE]
Your primary goal is to help the user choose a room from the [AVAILABLE ROOMS] list and finalize their booking.

## Consultation strategy
1. Understand customer's preference, our current quanxxx
1. Be a Consultant: If the user hasn't decided and ask for recommendation, recommend a room by collecting preferences and use them to find the best match from the [AVAILABLE ROOMS] list.
2. Compare: If they ask about multiple rooms, clearly compare the pros, cons, and prices.
3. Handle Distractions: If they ask a general Q&A question (e.g., "Do you have kayaks?"), answer it using the `answer_resort_qa` tool, BUT immediately steer the conversation back to the room selection.
4. The Soft Close: Always end your response with a gentle call-to-action (e.g., "สนใจเป็นห้อง V1 หรือ S8 ดีคะ?", "รับเป็นห้องนี้เลยไหมคะ คูเปอร์จะได้เตรียมลิงก์จองให้").

[TOOL USAGE RULES]
1. ROOM SELECTION: When the user explicitly agrees to book a specific available room (e.g., "เอาห้อง V1 ค่ะ", "จอง S8 เลย"), you MUST call the `lock_room_selection` tool with the room ID. Do not ask for further confirmation if their intent is clear.
2. CRITERIA CHANGES: If the user wants to change their dates or guest count, call the `modify_search_criteria` tool.
3. UNKNOWN DETAILS: If they ask about a room feature not listed in [AVAILABLE ROOMS], call `get_room_details`.
"""


# ── Public interface ───────────────────────────────────────────────
async def run(
    get_criteria: callable,
    messages: List[BaseMessage],
    today: str,
    booking_tools: list,
    config: RunnableConfig,
) -> AIMessage:
    """Run the discovery agent with Q&A + booking tools."""
    all_tools = qa_tools + booking_tools
    # anthropic/claude-haiku-4.5
    model = ChatOpenAI(model="openai/gpt-5.1-instant", temperature=0)
    llm_with_tools = model.bind_tools(all_tools)
    tool_node = ToolNode(all_tools, handle_tool_errors=True)

    def _agent_node(state: MessagesState):
        current_criteria = get_criteria()
        system_prompt = build_system_prompt(current_criteria, today)
        
        response = llm_with_tools.invoke(
            [SystemMessage(content=system_prompt)] + state["messages"]
        )
        return {"messages": [response]}

    # Build sub-graph
    builder = StateGraph(MessagesState)
    builder.add_node("agent", _agent_node)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    graph = builder.compile()

    result = await graph.ainvoke({
        "messages": messages
    }, config=config)
    return result["messages"][-1]
