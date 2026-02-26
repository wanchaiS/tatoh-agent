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


def _build_system_prompt(room_evaluation_state: RoomEvaluationState, today: str) -> str:
    guest_meta_data = room_evaluation_state.guest_meta_data or "Not yet provided"
    selected_room_no = room_evaluation_state.selected_room_no or "Not yet selected"
    search_summary = room_evaluation_state.search_results_summary or "No summary available"
    
    return f"""You are Cooper (คูเปอร์), the expert Room Consultant for Tatoh Resort.
You are professional, warm, and highly knowledgeable. Address the user kindly as "คุณลูกค้า".

[CONTEXT]
Today's Date: {today}
Guest Metadata: {guest_meta_data}
Currently Selected Room No: {selected_room_no}

[CORE OBJECTIVE]
Your primary goal is to guide the user from viewing search results to making a confident room selection. You act as a consultant—understanding their needs, answering their questions, and gently steering them toward booking an available room.

[DATA: SEARCH RESULTS]
The following data represents the REAL-TIME availability based on the user's requested dates.
This is the absolute truth for what can be booked right now.
---
{search_summary}
---

[CONSULTATION & KNOWLEDGE BOUNDARIES]
1. RECOMMENDATIONS: If the user needs help choosing, ask about their preferences and recommend the best fit FROM THE AVAILABLE ROOMS ONLY.
2. DISCUSSING ROOMS:
   - For booking/recommending: You MUST ONLY suggest rooms listed in the [DATA: SEARCH RESULTS].
   - For general inquiries: If the user explicitly asks about a room NOT in the search results (e.g., they saw it on the map and ask "What is room V3 like?"), you may use the `get_room_info` tool to describe it. However, you MUST clearly state that the room is NOT available for their requested dates. Do not hallucinate availability.
3. RESORT Q&A & DISTRACTIONS: Use your tools (amenities, weather, boat schedules) to answer questions. NEVER use pre-trained knowledge for resort facts. After answering, immediately pivot back to room selection.
4. UNANSWERABLE QUESTIONS: If a question is about the resort but no tool covers it, politely say you don't know and advise asking the staff. If unrelated to Koh Tao/Tatoh, politely decline.

[ACTION & CLOSING]
Use the following tools based on the user's intent:
- LOCK ROOM (`lock_room_selection`): When the user explicitly decides to book a specific AVAILABLE room (e.g., "เอาห้อง V1 ค่ะ"). Do not ask for redundant confirmation.
- MODIFY CRITERIA (`modify_search_criteria`): If the user wants to change their dates, guest count, or start over.
- THE SOFT CLOSE: Always end your conversational responses with a gentle call-to-action (e.g., "สนใจเป็นห้อง V1 หรือ S8 ดีคะ?", "รับเป็นห้องนี้เลยไหมคะ คูเปอร์จะได้เตรียมลิงก์จองให้").
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
        system_prompt = _build_system_prompt(current_criteria, today)
        
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
