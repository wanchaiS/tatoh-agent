from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from typing import List
import json

from agent.criteria_discovery.schema import Criteria
from agent.shared_tools.common_tool_usage_rules import common_tool_usage_rules
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
    ask_for_clarification,
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
    ask_for_clarification,
]


def build_system_prompt(criteria: Criteria, today: str) -> str:
    # `exclude_none=True` now strips out empty fields AND the default None booleans
    criteria_summary = json.dumps(criteria.model_dump(exclude_none=True), indent=2)
    missing_fields = criteria.get_missing_fields()
    missing_info = ', '.join(missing_fields) if missing_fields else 'None — all criteria collected!'
    
    return f"""You are Cooper (คูเปอร์), the welcoming first point of contact for Tatoh Resort, Koh Tao.
Address the user kindly as "คุณลูกค้า" when speaking Thai.

{common_tool_usage_rules}

[CONTEXT]
Today's Date: {today}
Current Booking State: {criteria_summary if criteria_summary != '{{}}' else 'No booking info yet.'}
Still Missing: {missing_info}

[CORE DIRECTIVE]
Your primary goal right now is strictly TO GATHER INFORMATION. You must collect all booking criteria before we can actually check room availability.

[RESPONSE FORMULA]
To ensure a smooth and natural conversation, you MUST structure every single response using this exact formula:

Step 1: Answer Questions & Acknowledge
- If the user asked questions, answer them using the tools provided. 
- If multiple tools were called (e.g. `get_room_info` AND `no_tool_found`), you must combine their outputs naturally. (e.g. "Room S8 is beautiful, but I don't have information about a pool"). NEVER guess resort details.
- If the user provided booking criteria (dates/guests), acknowledge them warmly, and blindly call `extract_booking_criteria`.

Step 2: The Pivot (Nudge)
- Check the 'Still Missing' list (from the state above, or from the output of the `extract_booking_criteria` tool if you just called it).
- If there are STILL MISSING fields, you MUST end your message by smoothly pivoting to ask for them. 
- Example of a good Step 1 + Step 2 combination: "สำหรับห้อง S8 จะเป็นวิวทะเลค่ะ ส่วนเรื่องสระว่ายน้ำทางเราไม่มีข้อมูลนะคะ เพื่อให้คูเปอร์เช็คห้องว่างให้ได้ ไม่ทราบว่าคุณลูกค้าจะเข้าพักวันที่เท่าไหร่ และมากี่ท่านคะ?"

Step 3: Transition (Only if done)
- If the 'Still Missing' list is 'None' (all info gathered), DO NOT ask any more questions. Tell the user you are looking up rooms and call `proceed_to_room_search`.
"""


# ── Public interface ───────────────────────────────────────────────
def run(
    criteria: Criteria,
    messages: List[BaseMessage],
    today: str,
    booking_tools: list,
) -> AIMessage:
    """Run the discovery agent with Q&A + booking tools."""
    all_tools = qa_tools + booking_tools

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = model.bind_tools(all_tools)
    tool_node = ToolNode(all_tools, handle_tool_errors=True)

    def _agent_node(state: MessagesState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # Build sub-graph
    builder = StateGraph(MessagesState)
    builder.add_node("agent", _agent_node)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    graph = builder.compile()

    system_prompt = build_system_prompt(criteria, today)
    result = graph.invoke({
        "messages": [SystemMessage(content=system_prompt)] + messages
    })
    return result["messages"][-1]
