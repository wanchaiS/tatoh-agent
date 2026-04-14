from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from agent.context.agent_service_provider import AgentServiceProvider
from agent.model import tool_node
from agent.nodes.agent import agent_node
from agent.nodes.context import context_node
from agent.nodes.ui import push_pending_search_results_ui_node
from agent.state import State

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
