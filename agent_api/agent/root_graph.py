from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent.agent_node import agent_node
from agent.prompts import PHASE_TOOLS
from agent.types import GlobalState


def route_after_agent(state: GlobalState):
    """Route: tool calls → tools, rooms found in discovery → transition, else → END."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"

    return END


# Collect all tools across phases (deduplicate by name)
_seen = set()
all_tools = []
for tools in PHASE_TOOLS.values():
    for tool in tools:
        if tool.name not in _seen:
            _seen.add(tool.name)
            all_tools.append(tool)

tool_node = ToolNode(all_tools, handle_tool_errors=True)

graph_builder = StateGraph(GlobalState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent", route_after_agent,
    {"tools": "tools", END: END}
)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()
