from agent.tools.exceptions import ToolValidationError
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode, tools_condition
from datetime import datetime,date, timedelta
from langchain_core.runnables import RunnableConfig
from dataclasses import dataclass
from langgraph.graph.ui import push_ui_message, AnyUIMessage, ui_message_reducer
from typing import Sequence, Annotated, Literal, Dict, TypedDict
import uuid


from agent.tools.exceptions import ToolValidationError
from agent.context.agent_service_provider import get_agent_service_provider
from agent.tools.search_available_rooms import RoomAvailabilityResult, search_available_rooms
from db.models import Room
                                                                                                                                                                                                                                                                                     

def append_search_results(
    existing: list[RoomAvailabilityResult] | None, 
    new: list[RoomAvailabilityResult] | Literal["clear"] | None
) -> list[RoomAvailabilityResult]:
    
    # 1. Allow the processing node to clear the state
    if new == "clear":
        return []

    # 2. Handle missing initial states safely
    if existing is None:
        existing = []

    if new is None:
        return existing

    return existing + new

class RoomCard(TypedDict):
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
    date_ranges: list[dict[str, str]]

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

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pending_render_search_results: Annotated[list[RoomAvailabilityResult], append_search_results]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    rooms: Dict[str, InternalRoom]


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

    Today is {today}
    Resort's possible rooms are: {rooms}
    Resort's possible room types are: {room_types}

    ## Knowledge Rules                                                                                                                                                                                                                                                                     

    Always check available tools first before answering.                                                                                                                                                                                                                                   
    - **Hotel questions** (rooms, availability, pricing, bookings, resort facilities): Use tools only. If no tool can answer it, say "I don't have that information — please contact us directly."                                                                                         
    - **Koh Tao questions** (island, activities, diving, transport, local tips): Use tools first. If no tool applies, you may draw on general knowledge.                                                                                                                                   
    - **Anything else**: Only answer if you have a tool for it. Otherwise, say you cannot help with that.                                                                                                                                                                                  

    ## Room Availability Search Directives
    - The tool search_available_rooms have 3 types of response:
    1. a result text message, this is a result of search, weather rooms found or not
    2. a tool validation error, this is a business rule violation
    3. a system error, this is a system error that could be network, or any exception
    when rooms found with no expansion, response which room they would like to book.
    when rooms found with expansion, response with expansion dates info in short sentence.
    when no rooms found, just reponse short sentence based on tool's response naturally.
    when tool validation error, follow the instruction in the tool response naturally.
    when system error, gracefully apologize and suggest to contact hotel directly.

    ### Date Time Rules
    - search dates should not be in the past, ask user to provide new dates.
    - when dates are ambiguous, you can guess a sensible date range, and ask user to confirm.

    Examples:
    Tool response: "No room available, room combination may work, ask if they want mix and match, and pls provide guest number"
    Agent response: "ช่วงวันที่คุณลูกค้าต้องการ ไม่มีห้องว่างแบบติดต่อกันเลยค่ะ สนใจพักแบบสลับห้องไหมค่ะ พักกี่ท่านค่ะ จะได้เช็คให้"

    
    
    ## RESPONSE TONE & STYLE
    Act like a warm, experienced hotel receptionist — not a system or search engine.
    1. Never output system variable names to the user.
    2. When Ask for missing info, ask naturally in one sentence. Don't narrate internal actions.
    3. Never fabricate hotel data. Never confirm or imply you checked something you did not. 
"""

def get_prompt(state: State) -> str:
    room_names = [room.room_name for room in state["rooms"].values()]
    room_types = [room.room_type for room in state["rooms"].values()]
    return system_prompt.format(
        today=datetime.now().strftime("%Y-%m-%d"),
        rooms=room_names,
        room_types=room_types,
    )


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
    
    # populate room card
    room_cards: list[RoomCard] = []
    for room_name, dates in merged.items():
        room = state["rooms"][room_name]
        room_cards.append({
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
            "date_ranges": dates_to_ranges(dates),
        })
    
    # last ai message
    last_ai_message = state["messages"][-1]

    push_ui_message(
        name="search_results",
        props= {"rooms": room_cards}, 
        id=str(uuid.uuid4()), 
        message=last_ai_message
    )
    
    return {
        "pending_render_search_results": "clear",
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

async def context_node(state: State,config: RunnableConfig):
    """
    context that can be re-used in the graph, to avoid re-fetch data from database
    """
    room_service = get_agent_service_provider(config).room_service
    rooms: list[Room] = await room_service.get_all_rooms()
    thumbnail_urls = await room_service.get_first_photo_urls(room_ids=[room.id for room in rooms])

    internal_room_dict: dict[str, InternalRoom] = {}
    for room in rooms:
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
            thumbnail_url=thumbnail_urls.get(room.id) or "",
        )
    return {"rooms": internal_room_dict}

graph = StateGraph(State)  # pyrefly: ignore[bad-specialization]
graph.add_node("context", context_node)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("push_pending_search_results_ui", push_pending_search_results_ui_node)
graph.add_edge(START, "context")
graph.add_edge("context", "agent")
graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "push_pending_search_results_ui"})
graph.add_edge("tools", "agent")
graph.add_edge("push_pending_search_results_ui", END)

