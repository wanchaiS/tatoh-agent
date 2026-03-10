from langgraph.graph import END, START, StateGraph

from agent.closing.node import closing_node
from agent.criteria_discovery.node import criteria_discovery_node
from agent.language_detection import language_detection_node
from agent.rooms_searching.node import room_searching_node
from agent.types import GlobalState
from agent.ui_cleanup import ui_cleanup_node


def get_node_by_phase(state: GlobalState):
    phase = state.get("phase") or "criteria_discovery"
    phase_map = {
        "criteria_discovery": "criteria_discovery_node",
        "room_searching": "room_searching_node",
        "closing": "closing_node",
    }
    node = phase_map.get(phase)
    if not node:
        raise ValueError(f"Invalid phase: {phase}")
    return node


graph_builder = StateGraph(GlobalState)

graph_builder.add_node("ui_cleanup_node", ui_cleanup_node)
graph_builder.add_node("language_detection_node", language_detection_node)
graph_builder.add_node("criteria_discovery_node", criteria_discovery_node)
graph_builder.add_node("room_searching_node", room_searching_node)
graph_builder.add_node("closing_node", closing_node)

graph_builder.add_edge(START, "ui_cleanup_node")
graph_builder.add_edge("ui_cleanup_node", "language_detection_node")
graph_builder.add_conditional_edges(
    "language_detection_node",
    get_node_by_phase,
    {
        "criteria_discovery_node": "criteria_discovery_node",
        "room_searching_node": "room_searching_node",
        "closing_node": "closing_node",
    },
)

graph_builder.add_edge("closing_node", END)

graph = graph_builder.compile()
