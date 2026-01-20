from langchain_openai import ChatOpenAI
from agent.tools.check_room_availability import check_room_availability
from agent.tools.get_room_info import get_room_info
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.prebuilt import ToolNode
from datetime import datetime
from pathlib import Path

# Load the system prompt from markdown file
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
main_agent_prompt_path = PROMPTS_DIR / "main_agent.md"

with open(main_agent_prompt_path, "r", encoding="utf-8") as f:
    MAIN_AGENT_PROMPT_TEMPLATE = f.read()

# Define the model and tools
model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0
)

tools = [check_room_availability, get_room_info]
model_with_tools = model.bind_tools(tools)

# Define the state (inherited from MessagesState)
class AgentGlobalState(MessagesState):
    """Global state for the agent including chat history."""
    pass

def main_agent(state: AgentGlobalState):
    """Main agent node that handles the conversation logic."""
    
    system_prompt = SystemMessage(
        content=MAIN_AGENT_PROMPT_TEMPLATE.format(current_date=datetime.now().strftime('%Y-%m-%d'))
    )
    
    response = model_with_tools.invoke([system_prompt] + state["messages"])
    
    return {
        "messages": [response],
    }



def route_tools(state: AgentGlobalState):
    """Custom routing: If tool calls, go to tools. Else go to end."""
    # Handle both list-based and dict-based state
    if isinstance(state, list):
        messages = state
    else:
        messages = state.get("messages", [])
        
    if not messages:
        return "end"
        
    ai_message = messages[-1]
    
    # Check for tool_calls attribute and ensure it's not empty
    if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
        return "tools"
        
    return "end"

# Use the prebuilt ToolNode
tool_node = ToolNode(tools)

# Build the graph
workflow = StateGraph(AgentGlobalState)

# Add nodes
workflow.add_node("agent", main_agent)
workflow.add_node("tools", tool_node)

# Set entry point
workflow.add_edge(START, "agent")

# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    route_tools,
    {"tools": "tools", "end": END}
)

# After tools, always go back to the agent for feedback loop
workflow.add_edge("tools", "agent")



# Compile the graph
graph = workflow.compile()
