from langchain_openai import ChatOpenAI
from agent.tools.check_room_availability import check_room_availability
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from datetime import datetime

# Define the model and tools
model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0
)

tools = [check_room_availability]
model_with_tools = model.bind_tools(tools)

# Define the state (inherited from MessagesState)
class AgentGlobalState(MessagesState):
    """Global state for the agent including chat history."""
    pass

def main_agent(state: AgentGlobalState):
    """Main agent node that handles the conversation logic."""
    
    system_prompt = SystemMessage(
        content="""You are a helpful assistant for TATOH hotel. Help guests check room availability.

## Core Behavior

- Be conversational and warm
- Keep responses concise unless detail is requested
- If you need information to use a tool, ask the user naturally
- After getting tool results, summarize helpfully—don't just dump raw data

## Booking Flow
The current date is {current_date}. 
When a user wants to check availability but hasn't provided dates or guest count, ask for the missing information before calling the tool. Gather what you need in a natural way, not as a checklist.

## When Tools Return No Results

Offer alternatives based on tool result or ask if they'd like to adjust their search criteria.""".format(current_date=datetime.now().strftime('%Y-%m-%d'))
    )
    
    # Invoke model
    response = model_with_tools.invoke([system_prompt] + state["messages"])
    
    return {
        "messages": [response],
    }

# Use the prebuilt ToolNode
tool_node = ToolNode(tools)

# Build the graph
workflow = StateGraph(AgentGlobalState)

# Add nodes
workflow.add_node("agent", main_agent)
workflow.add_node("tools", tool_node)

# Set entry point
workflow.add_edge(START, "agent")

# Add conditional edges from agent to tools or END using the prebuilt tools_condition
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# After tools, always go back to the agent for feedback loop
workflow.add_edge("tools", "agent")

# Compile the graph
graph = workflow.compile()
