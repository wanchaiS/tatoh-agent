from agent.tools.exceptions import ToolValidationError
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime
from datetime import datetime,date, timedelta
from dataclasses import dataclass
from langgraph.graph.ui import push_ui_message, AnyUIMessage, ui_message_reducer
from typing import Sequence, Annotated, Dict, TypedDict
import uuid


from agent.tools.exceptions import ToolValidationError
from agent.context.agent_service_provider import AgentServiceProvider
from agent.tools.search_available_rooms import RoomAvailabilityResult, search_available_rooms
from db.models import Room
                                                                                                                                                                                                                                                                                     

class EmbeddedPhoto(TypedDict):
    url: str
    thumbnails: dict[int, str]  # {240: url, 480: url, 960: url}


class RoomCard(TypedDict):
    id: int
    room_name: str
    room_type: str
    summary: str
    bed_queen: int
    bed_single: int
    baths: int
    size: float
    price_weekdays: float
    price_weekends_holidays: float
    price_ny_songkran: float
    max_guests: int
    steps_to_beach: int
    sea_view: int
    privacy: int
    steps_to_restaurant: int
    room_design: int
    room_newness: int
    tags: list[str]
    thumbnail_url: str
    photos: list[EmbeddedPhoto]
    date_ranges: list[dict[str, str]]


MAP_SRC = "/static/photos/maps/resort_map.jpeg"

ROOM_PIN_POSITIONS: dict[int, dict[str, float]] = {
    18: {"x": 88.4, "y": 47.6},   # S1
    19: {"x": 66.5, "y": 47.4},   # S2
    20: {"x":  8.8, "y": 50.2},   # S3
    21: {"x": 25.6, "y": 69.7},   # S4
    22: {"x": 40.6, "y": 47.0},   # S5
    23: {"x": 44.0, "y": 85.6},   # S6
    24: {"x":  8.2, "y": 87.0},   # S7
    25: {"x": 70.7, "y": 68.3},   # S8
    26: {"x": 56.3, "y": 86.4},   # S9
    27: {"x":  9.7, "y": 36.7},   # S10
    28: {"x": 29.8, "y": 34.5},   # S11
    29: {"x": 61.5, "y": 38.0},   # S12
    30: {"x": 82.1, "y": 38.4},   # S14
    31: {"x": 26.1, "y": 87.2},   # V1
    32: {"x": 50.9, "y": 69.9},   # V2
    33: {"x": 92.9, "y": 58.8},   # V3
}


@dataclass
class InternalRoom:
    id: int
    room_name: str
    room_type: str
    summary: str
    bed_queen: int
    bed_single: int
    baths: int
    size: float
    price_weekdays: float
    price_weekends_holidays: float
    price_ny_songkran: float
    max_guests: int
    steps_to_beach: int
    sea_view: int
    privacy: int
    steps_to_restaurant: int
    room_design: int
    room_newness: int
    tags: list[str]
    thumbnail_url: str
    photos: list[EmbeddedPhoto]


def list_reducer(existing: list[str], update: dict) -> list[str]:
    """Custom reducer for list[str]: supports append, clear, remove."""
    if "clear" in update:
        return [] 

    if existing is None:
        existing = [] 

    if "append" in update:
        existing.extend(update["append"])
        return existing

    if "remove" in update:
        to_remove = update["remove"]
        return [x for x in existing if x != to_remove]  
    
    # do nothing
    return existing

# def dict_reducer(existing: dict, update: dict) -> dict:
#     if existing is None:
#         existing = {}
#     existing.update(update)
#     return existing

# class UserContext(BaseModel):
#     id: int
#     full_name: str
#     email: str
#     line: str
#     phone: str
#     payment_evidence_link:str

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pending_render_search_results: Annotated[list[RoomAvailabilityResult], list_reducer]
    pending_search_range: dict[str, str] | None  # {"start": ..., "end": ...}
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    rooms: Dict[str, InternalRoom] # no reducer, always replace
    # selected_rooms: Annotated[list[str], list_reducer]
    # confirmation_details_sent: bool
    # user_confirm_booking: bool
    # user_contact_info: Annotated[dict, dict_reducer]
    # user_context: dict
    # payment_confirmed: bool
    # user_contact_info_collected: bool
    # booking_created: bool
    


def tool_error_handler(error: Exception) -> str:
    match error:
        case ToolValidationError():
            return f"Tool validation error: {error}"
        case _:
            # Re-raise unexpected system errors, or return a graceful message
            return f"Unexpected system error: {error}"

tools = [search_available_rooms]
tool_node = ToolNode(tools, handle_tool_errors=tool_error_handler).with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True
)

_model_with_tools = None

def _get_model_with_tools():
    global _model_with_tools
    if _model_with_tools is None:
        from core.config import settings
        model = ChatOpenAI(
            model="openai/gpt-5.1-instant",
            temperature=0,
            streaming=True,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools

system_prompt = """
    You are Cooper (คูเปอร์), the hotel AI assistant for Tatoh Resort (ตาโต๊ะรีสอร์ท), Koh Tao.
    Always reply in the same language the user has been speaking. Address the user kindly as "คุณลูกค้า" when speaking Thai.

    ## Context
    Today is {today}
    Available room names: {rooms}
    Available room types: {room_types}

    ## Knowledge Rules                                                                                                                                                                                                                                                                     
    - Hotel questions (rooms, availability, pricing, bookings, resort facilities): Use tools only. If no tool can answer it, say "I don't have that information — please contact us directly."                                                                                         
    - Koh Tao questions (island, activities, diving, transport, local tips): Use tools first. If no tool applies, you may draw on general knowledge.                                                                                                                                   
    - Anything else Only answer if you have a tool for it. Otherwise, say you cannot help with that.                                                                                                                                                                                  
    - Never output system variable names to the user.
    - Never fabricate hotel data. Never confirm or imply you checked something you did not. 

    ## Room Availability Search Directives
    - When rooms found (no expansion): ask which room they'd like to book. Keep it short.
    - When rooms found (with expansion): briefly mention the expanded date window, then ask which room.
    - When no rooms found: respond naturally in one short sentence based on the tool's message.
    - When tool validation error: follow the instruction in the tool response naturally.
    - When system error: gracefully apologize and suggest contacting the hotel directly.

    ### Date Time Rules
    - If the derived date is in the past, assume the same date next year.
    - When building a date range, fill in any missing parts (day, month, year) from the most recent date range in the conversation:
      - User gives only a month → keep same day range, change month. e.g. prev: 14-17 July, user says "month 8" → August 14-17.
      - User gives only a day range → keep same month/year. e.g. prev: July 14-17, user says "20-23" → July 20-23.
      - User gives only a number of nights → keep same check-in, extend checkout.
    - When no prior dates exist in the conversation and month is not provided, assume current month and year.
    - If after applying the above the dates are still ambiguous, make a sensible guess and confirm with the user in one sentence.
    - When mentioning dates in your response, always include the year if it differs from the current year (e.g. "14-17 กุมภาพันธ์ 2027" not just "14-17 กุมภาพันธ์").

    ## Examples
    Tool: "Found 3 room(s) for 3 nights between 2026-08-14 and 2026-08-17."
    Agent: "มีห้องว่างช่วง 14-17 สิงหาคมค่ะ คุณลูกค้าสนใจห้องไหนเป็นพิเศษไหมคะ?"

    Tool: "No rooms available for the full duration on 2026-08-14 and 2026-08-17, but room combinations may work. guest_no is required."
    Agent: "ตอนนี้ไม่มีห้องที่ว่างติดกันในช่วง 14-17 แต่ถ้าสนใจพักแบบสลับห้อง ขอทราบจำนวนผู้เข้าพักได้ไหมค่ะ แล้วจะได้เช็คให้ค่ะ"

    Tool: "Found 2 room(s) that can be combined to accommodate 4 guests between 2026-08-14 and 2026-08-17. Let the user browse and pick the rooms they prefer."
    Agent: "มีห้องว่างแบบผสมช่วง 14-17 สิงหาคม ลองเลือกดูก่อนได้นะคะ"

    Tool: "Found 2 room(s) for 3 nights between 2026-08-9 and 2026-08-22 (window expanded by ±5 days)."
    Agent: "ไม่มีห้องว่างตรงช่วง 14-17 สิงหาคมนะคะ แต่ยังพอมีห้องว่างในช่วงใกล้เคียงค่ะ ลองดูก่อนนะคะ"

    Tool: "No rooms available for 3 nights between 2026-08-14 and 2026-08-17. Ask user if they want to try different dates."
    Agent: "ช่วงนั้นเต็มหมดเลยค่ะ ลองเปลี่ยนวันดูไหมคะ?"

    ## Response Tone & Style
    Act like a warm, experienced hotel receptionist — not a system or search engine. Be concise: 1-2 sentences per reply unless more detail is genuinely needed.
    - When asking for missing info, ask naturally in one sentence. Don't narrate internal actions.
"""

def get_prompt(state: State) -> str:
    room_names = [room.room_name for room in state["rooms"].values()]
    room_types = [room.room_type for room in state["rooms"].values()]
    return system_prompt.format(
        today=datetime.now().strftime("%Y-%m-%d"),
        # phase=get_phase(state),
        rooms=room_names,
        room_types=room_types,
        # selected_room=str(state["selected_rooms"]),
        # confirmation_details_sent=str(state["confirmation_details_sent"]),
        # booking_confirmed=str(state["user_confirm_booking"]),
        # payment_evidence_provided=str(state["user_context"]["payment_evidence_link"]),
        # payment_evidence_confirmed=str(state["payment_confirmed"]),
        # user_contact_info_collected=str(state["user_contact_info_collected"]),
    )

# def get_phase(state: State) -> str:
#     # user has never selected any room
#     if not state["selected_rooms"]:
#         return "Discovery"
    
#     if not state["user_confirm_booking"]:
#         return "BookingConfirmation"
    
#     # collect user info before payment, at this point having contact info is helpful
#     # in case anything goes wrong, staff can handle it with this info
#     if not state["user_contact_info_collected"]:
#         return "ContactInfo"
    
#     if not state["payment_confirmed"]:
#         return "Payment"
    
#     # create booking record
#     if not state["booking_created"]:
#         return "BookingCreation"
    
#     return "Completed"

async def agent_node(state: State) -> dict:
    """
        main agent node
    """
    prompt = get_prompt(state)
    response = await _get_model_with_tools().ainvoke([SystemMessage(content=prompt)] + state["messages"])

    return {"messages": [response]}



def push_pending_search_results_ui_node(state: State):
    pending_search_results = state["pending_render_search_results"]
    if not pending_search_results:
        return
    
    # merge rooms
    merged = {}
    for result_dict in pending_search_results:
        for room_name, dates in result_dict.items():
            if room_name not in merged:
                merged[room_name] = set(dates)
            else:
                merged[room_name].update(set(dates))
    
    # populate room cards
    room_cards: list[RoomCard] = []
    for room_name, dates in merged.items():
        room = state["rooms"][room_name]
        room_cards.append({
            "id": room.id,
            "room_name": room.room_name,
            "room_type": room.room_type,
            "summary": room.summary,
            "bed_queen": room.bed_queen,
            "bed_single": room.bed_single,
            "baths": room.baths,
            "size": room.size,
            "price_weekdays": room.price_weekdays,
            "price_weekends_holidays": room.price_weekends_holidays,
            "price_ny_songkran": room.price_ny_songkran,
            "max_guests": room.max_guests,
            "steps_to_beach": room.steps_to_beach,
            "sea_view": room.sea_view,
            "privacy": room.privacy,
            "steps_to_restaurant": room.steps_to_restaurant,
            "room_design": room.room_design,
            "room_newness": room.room_newness,
            "tags": room.tags,
            "thumbnail_url": room.thumbnail_url,
            "photos": room.photos,
            "date_ranges": dates_to_ranges(dates),
        })

    map_data = {
        "src": MAP_SRC,
        "pins": ROOM_PIN_POSITIONS,
    }
    search_range = state.get("pending_search_range") or {}

    # last ai message
    last_ai_message = state["messages"][-1]

    push_ui_message(
        name="search_results",
        props={"rooms": room_cards, "map": map_data, "search_range": search_range},
        id=str(uuid.uuid4()),
        message=last_ai_message
    )

    return {
        "pending_render_search_results": "clear",
        "pending_search_range": None,
    }

def dates_to_ranges(dates: set[str]) -> list[dict[str, str]]:                                                                                                                                                                                                                          
    if not dates:                                                                                                                                                                                                                                                                      
        return []                                                                                                                                                                                                                                                                      
    sorted_dates = sorted(dates)                                                                                                                                                                                                                                                       
    ranges: list[dict[str, str]] = []
    start = end = sorted_dates[0]                                                                                                                                                                                                                                                      
    for d in sorted_dates[1:]:                        
        end_next = date.fromisoformat(end) + timedelta(days=1)
        if date.fromisoformat(d) == end_next:                                                                                                                                                                                                                                          
            end = d
        else:                                                                                                                                                                                                                                                                          
            ranges.append({"start": start, "end": end})
            start = end = d                                                                                                                                                                                                                                                            
    ranges.append({"start": start, "end": end})       
    return ranges

async def context_node(state: State, runtime: Runtime[AgentServiceProvider]):
    """
    context that can be re-used in the graph, to avoid re-fetch data from database
    """
    room_service = runtime.context.room_service
    rooms: list[Room] = await room_service.get_all_rooms()
    room_ids = [room.id for room in rooms]
    all_photos = await room_service.get_all_photos_for_rooms(room_ids=room_ids)

    internal_room_dict: dict[str, InternalRoom] = {}
    for room in rooms:
        photos = all_photos.get(room.id, [])
        thumbnail_url = photos[0]["thumbnails"][240] if photos else ""
        internal_room_dict[room.room_name.lower()] = InternalRoom(
            id=room.id,
            room_name=room.room_name,
            room_type=room.room_type,
            summary=room.summary,
            bed_queen=room.bed_queen,
            bed_single=room.bed_single,
            baths=room.baths,
            size=room.size,
            price_weekdays=room.price_weekdays,
            price_weekends_holidays=room.price_weekends_holidays,
            price_ny_songkran=room.price_ny_songkran,
            max_guests=room.max_guests,
            steps_to_beach=room.steps_to_beach,
            sea_view=room.sea_view,
            privacy=room.privacy,
            steps_to_restaurant=room.steps_to_restaurant,
            room_design=room.room_design,
            room_newness=room.room_newness,
            tags=room.tags.split(",") if room.tags else [],
            thumbnail_url=thumbnail_url,
            photos=photos,
        )
    return {"rooms": internal_room_dict}

graph = StateGraph(State, context_schema=AgentServiceProvider)  # pyrefly: ignore[bad-specialization]
graph.add_node("context", context_node)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("push_pending_search_results_ui", push_pending_search_results_ui_node)
graph.add_edge(START, "context")
graph.add_edge("context", "agent")
graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "push_pending_search_results_ui"})
graph.add_edge("tools", "agent")
graph.add_edge("push_pending_search_results_ui", END)

