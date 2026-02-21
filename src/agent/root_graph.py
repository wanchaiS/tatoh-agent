from langgraph.graph import StateGraph, START, END

from agent.types import GlobalState
from agent.criteria_discovery.node import criteria_discovery_node
from agent.room_evaluation.node import evaluate_options_node


def get_node_by_phase(state: GlobalState):
    phase = state.get("phase") or "criteria_discovery"

    phase_map = {
        "criteria_discovery": "criteria_discovery_node",
        "evaluate_options": "evaluate_options_node",
        "payment_settlement": "payment_settlement_node",
        "contact_info_collection": "contact_info_collection_node",
        "summarize_booking": "summarize_booking_node"
    }

    node = phase_map.get(phase)

    # should never happen
    if not node:
        raise ValueError(f"Invalid phase: {phase}")

    return node

def booking_phase_classifier(state: GlobalState):
    """Node function: does nothing, just a routing checkpoint."""
    pass


graph_builder = StateGraph(GlobalState)

# 1. Add Nodes
graph_builder.add_node("booking_phase_classifier", booking_phase_classifier)
graph_builder.add_node("criteria_discovery_node", criteria_discovery_node)
graph_builder.add_node("evaluate_options_node", evaluate_options_node)

# 2. Define Edges
graph_builder.add_edge(START, "booking_phase_classifier")
graph_builder.add_conditional_edges("booking_phase_classifier", get_node_by_phase, {
        "criteria_discovery_node": "criteria_discovery_node",
        "evaluate_options_node": "evaluate_options_node"
    })

# After sub-graphs finish, they go to END
graph_builder.add_edge("evaluate_options_node", END)
graph_builder.add_edge("criteria_discovery_node", END)

graph = graph_builder.compile()
