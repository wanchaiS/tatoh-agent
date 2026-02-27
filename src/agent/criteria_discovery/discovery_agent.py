from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from datetime import datetime
import json

from agent.criteria_discovery.schema import Criteria
from agent.types import GlobalState
from agent.shared_tools import (
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
)
from agent.criteria_discovery.tools.booking_tools import booking_tools

# ── Shared Q&A tools (always available) ──────────────────────────
qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
]


def build_system_prompt(criteria: Criteria, today: str) -> str:
    # `exclude_none=True` now strips out empty fields AND the default None booleans
    criteria_summary = json.dumps(criteria.model_dump(exclude_none=True), indent=2)
    criteria_summary = criteria_summary if criteria_summary != {} else 'None yet.'

    return f"""You are Cooper (คูเปอร์), the welcoming first point of contact for Tatoh Resort (ตาโต๊ะรีสอร์ท), Koh Tao.
Address the user kindly as "คุณลูกค้า" when speaking Thai.

[CONTEXT]
Today's Date: {today}
Current Booking State: {criteria_summary}

[CORE DIRECTIVE]
Your primary goal is TO GATHER INFORMATION and answer questions. You must collect all booking criteria before we can check room availability.

[TOOL USAGE RULES (CRITICAL)]
You are responsible for orchestrating tools. You can call multiple tools if needed.
1. STATE UPDATES & CHANGES: If the user provides ANY booking details, OR asks to change/update previously provided details (e.g., "เปลี่ยนเป็นพฤษภา", "เอาเป็น 5 คืน"), you MUST call the `extract_booking_criteria` tool. Do not just acknowledge the change in text; you must call the tool to update the system.
2. RESORT Q&A: Use your specific lookup tools for room details, prices, policies, amenities, and activities. NEVER use pre-trained knowledge for resort facts.
3. NO TOOL APPLIES:
   - Resort question but no tool covers it → Politely inform that you do not have the information but yhey can ask the staff.
   - Unrelated to Tatoh Resort/Koh Tao → Politely inform that you cannot help with that.
   - General Koh Tao island question (weather, travel tips) → answer from general knowledge.

[RESPONSE TONE & STYLE]
You MUST act like a human receptionist, not a robot or a system form.
1. NEVER output system variables (e.g., `total_guests`, `duration_nights`) to the user.
2. DO NOT use bullet points to ask for missing info.
3. MULTI-INTENT HANDLING: If the user asks a question AND provides dates, answer the question first, then smoothly transition. (You must also call both the Q&A tool and the extraction tool in the background).
4. ASKING FOR INFO: Gently ask for the missing pieces of information at the very end of your response in a single, natural, flowing sentence. (e.g., "สำหรับเข้าพักช่วงวันที่ 25-29 รบกวนขอทราบจำนวนผู้เข้าพัก และจำนวนคืนที่ต้องการพักด้วยนะคะ คูเปอร์จะได้เช็คห้องว่างให้ค่ะ")
5. READY TO SEARCH: When you receive the "All required criteria collected!" message from the extraction tool, do not ask any more questions. Politely confirm the final booking details and let the user know you will check the room availability for them now. Do NOT wait for the user to reply.

[AMBIGUITY RESOLUTION]
- If the Current Booking State shows `"is_year_ambiguous": true`, you MUST explicitly ask the user to confirm the year (e.g., "เป็นช่วงเดือนมกราคม ปี 2027 ถูกต้องไหมคะ?").
- Once the user replies (e.g., "ใช่ค่ะ" or "ไม่ใช่ค่ะ ปีนี้"), you MUST call the `resolve_ambiguous_year` tool and pass in the correct year. Do not call the general extraction tool for this simple confirmation.
"""


# ── Static sub-graph on GlobalState ──────────────────────────────
all_tools = qa_tools + booking_tools
_model = ChatOpenAI(model="openai/gpt-5.1-instant", temperature=0)
_llm_with_tools = _model.bind_tools(all_tools)
_tool_node = ToolNode(all_tools, handle_tool_errors=True)


def _agent_node(state: GlobalState):
    today = datetime.now().strftime("%Y-%m-%d")
    criteria = state.get("criteria") or Criteria()
    system_prompt = build_system_prompt(criteria, today)
    response = _llm_with_tools.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    return {"messages": [response]}


_builder = StateGraph(GlobalState)
_builder.add_node("discovery_agent", _agent_node)
_builder.add_node("tools", _tool_node)
_builder.add_edge(START, "discovery_agent")
_builder.add_conditional_edges("discovery_agent", tools_condition)
_builder.add_edge("tools", "discovery_agent")

criteria_discovery_graph = _builder.compile()
