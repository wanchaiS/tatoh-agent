from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from agent.types import GlobalState
import json

from agent.shared_tools import find_boat_schedules, get_gopro_service_info, get_kohtao_arrival_guide, get_room_gallery, get_room_info

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


def rooms_evaluation_node(state: GlobalState):
    evaluation_state = state.get("room_evaluation_state")
    search_results_summary = getattr(evaluation_state, "search_results_summary", None) if evaluation_state else None

    system_prompt = SystemMessage(content=f"""
        You are the Tatoh Resort Booking Consultant.
        Your goal is to help the user evaluate their options and commit to a booking.

        [SEARCH RESULTS]
        {search_results_summary}
        
        ## RULES:
        - If the user just arrived in this phase, you should immediately inform them of the search results found above.
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
builder = StateGraph(GlobalState)
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
    
    # Safely extract messages resulting from the graph
    out_messages = result.get("messages", [])
    new_message = out_messages[-1] if out_messages else None
    
    # Ensure all state updates from the sub-graph are returned
    return {
        "messages": [new_message] if new_message else [],
        "booking_context": result.get("booking_context", state.get("booking_context")),
        "room_evaluation_state": result.get("room_evaluation_state", state.get("room_evaluation_state"))
    }

def handle_adjust_criteria():
    pass