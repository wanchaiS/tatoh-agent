from langgraph.graph import StateGraph, START, END

from agent.types import GlobalState
from agent.criteria_discovery.node import criteria_discovery_node
from agent.rooms_searching.node import room_searching_node
from agent.room_evaluation.node import room_evaluation_node


def get_node_by_phase(state: GlobalState):
    phase = state.get("phase") or "criteria_discovery"
    phase_map = {
        "criteria_discovery": "criteria_discovery_node",
        "room_searching": "room_searching_node",
        "evaluate_options": "evaluate_options_node",
        "payment_settlement": "payment_settlement_node",
        "contact_info_collection": "contact_info_collection_node",
        "summarize_booking": "summarize_booking_node"
    }
    node = phase_map.get(phase)
    if not node:
        raise ValueError(f"Invalid phase: {phase}")
    return node


graph_builder = StateGraph(GlobalState)

graph_builder.add_node("criteria_discovery_node", criteria_discovery_node)
graph_builder.add_node("room_searching_node", room_searching_node)
graph_builder.add_node("room_evaluation_node", room_evaluation_node)

graph_builder.add_conditional_edges(START, get_node_by_phase, {
        "criteria_discovery_node": "criteria_discovery_node",
        "room_searching_node": "room_searching_node",
        "room_evaluation_node": "room_evaluation_node"
    })

graph_builder.add_edge("room_evaluation_node", END)

graph = graph_builder.compile()
