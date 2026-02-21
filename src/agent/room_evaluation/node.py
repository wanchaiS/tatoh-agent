from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
import json
from agent.types import GlobalState

from agent.shared_tools import find_boat_schedules, get_gopro_service_info, get_kohtao_arrival_guide, get_room_gallery, get_room_info
from agent.room_evaluation.search import run_search
from agent.room_evaluation.schema import RoomEvaluationState
    
qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_room_gallery,
    get_room_info,
]

tool_node = ToolNode(qa_tools, handle_tool_errors=True)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model_with_tools = model.bind_tools(qa_tools)


def rooms_evaluation_node(state: GlobalState):
    """
    This node is responsible for:
    1. Searching for rooms when criteria change detected or no current criteria id
    2. Assist user to evaluate the room options and commit to a booking.
    """
    
    discovery_state = state.get("criteria_discovery_state")
    room_eval_state = state.get("room_evaluation_state")

    # search rooms when criteria change detected or no current criteria id
    current_id = room_eval_state.current_criteria_id
    if discovery_state and (not current_id or current_id != discovery_state.get_criteria_id()):
        
        search_result = run_search(discovery_state)

        # Update context
        booking_context = state.get("booking_context", {})
        booking_context["search_results"] = [r.__dict__ for r in search_result.rooms]
        booking_context["expanded_days"] = search_result.expanded_days
        booking_context["exhausted"] = search_result.exhausted
        
        # Mark as searched for this criteria
        return {
            "booking_context": booking_context,
            "room_evaluation_state": {"current_criteria_id": discovery_state.get_criteria_id()}
        }


    booking_context = state.get("booking_context", {})
    formatted_context = json.dumps(booking_context, indent=2)

    system_prompt = SystemMessage(content=f"""
        You are the Tatoh Resort Booking Consultant.
        Your goal is to help the user evaluate their options and commit to a booking.
        
        ## CURRENT BOOKING CONTEXT:
        {formatted_context}
        
        ## RULES:
        - Use the tools to provide accurate info about rooms, views, and services.
        - Be consultative: If a room is better for families or sunrises, mention it.
        - Gently nudge the user towards selecting a room if they seem happy with the info.
        - Answer in the same language as the user.
        - Keep it concise and natural.
    """)

    messages = [system_prompt] + state["messages"]
    response = model_with_tools.invoke(messages)

    return {"messages": [response]}

# Build sub-graph
builder = StateGraph(RoomEvaluationState)
builder.add_node("evaluate_agent", rooms_evaluation_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "evaluate_agent")
builder.add_conditional_edges("evaluate_agent", tools_condition)
builder.add_edge("tools", "evaluate_agent")

evaluate_options_graph = builder.compile()

def evaluate_options_node(state: GlobalState):
    """Entry point for the evaluation sub-graph"""
    inputs = {
        "messages": state["messages"],
        "booking_context": state.get("booking_context", {}),
        "criteria_discovery_state": state.get("criteria_discovery_state"),
        "room_evaluation_state": state.get("room_evaluation_state")
    }
    result = evaluate_options_graph.invoke(inputs)
    # Ensure all state updates from the sub-graph are returned
    return {
        "messages": [result["messages"][-1]],
        "booking_context": result.get("booking_context", state.get("booking_context")),
        "room_evaluation_state": result.get("room_evaluation_state", state.get("room_evaluation_state"))
    }

def handle_adjust_criteria():
    pass