from langchain_openai import ChatOpenAI
from agent.tools.check_room_availability import check_room_availability
from agent.tools.get_room_info import get_room_info
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.prebuilt import ToolNode
from datetime import datetime


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
        content="""You are a helpful assistant for TATOH hotel. Help guests check room availability.
    
    ## Core Behavior
    - Be conversational and warm.
    - Keep responses concise unless detail is requested.
    - AFTER getting tool results, summarize helpfully—don't just dump raw data.
    
    ## Booking Flow & Strict Requirements
    The current date is {current_date}. 
    
    > [!IMPORTANT]
    > **CRITICAL RULE**: NEVER guess or assume `guests`, `checkInDate`, or `checkOutDate`. 
    > If a user provides a month (e.g., "เดือน 5") without a specific start/end date or guest count, YOU MUST ASK for clarification before calling any availability tools.
    
    - Gather what you need in a natural, warm way (e.g., "สนใจเข้าพักกี่ท่าน และช่วงวันที่เท่าไหร่ในเดือนพฤษภาคมดีคะ?").
    - Do not call `check_room_availability` until you have:
        1. Number of guests.
        2. Specific Check-in date.
        3. Specific Check-out date.
    
    ## Few-Shot Examples
    
    **User:** "ห้องว่างวันไหนบ้างคะ เดือน5"
    **Agent:** "ในเดือนพฤษภาคมปีนี้ คุณลูกค้าสนใจเข้าพักช่วงวันที่เท่าไหร่ถึงเท่าไหร่ และมากันทั้งหมดกี่ท่านคะ? เดี๋ยวหนูเช็คห้องที่ว่างที่สุดให้ค่ะ"
    
    **User:** "มีห้องว่างไหมครับ อาทิตย์หน้า"
    **Agent:** "อาทิตย์หน้าพอจะมีห้องว่างอยู่บ้างค่ะ เพื่อความแม่นยำ รบกวนขอทราบวันที่คุณลูกค้าสะดวกเช็คอิน-เช็คเอาท์ และจำนวนผู้เข้าพักนิดนึงนะคะ"
    
    ## Response Format
    When outputting room availability, you must use the following format for each room type:
    
    ### {{Room Name}}
    ![{{Room Name}}]({{image_token}})
    มี {{count}} ห้องพักให้เลือก 
    {{Room Numbers e.g. S3 / S4 / S5}}
    
    * {{price_weekdays}} THB for 1 night * จันทร์ -ศุกร์ *
    * {{price_weekends}} THB for 1 night * เสาร์ -  อาทิตย์ - วันหยุดนักขัตฤกษ์ *
    * {{price_high_season}} THB for 1 night * เทศกาลสงกรานต์และปีใหม่ *
    
    สำหรับ  {{capacity}}  ท่าน พร้อมอาหารเช้า 
    
    ## Alternatives
    If providing alternative rooms, use the same format above but ADD a line for available dates:
    "**วันที่ว่าง:** {{dates}}" in readable format (right after room numbers).
    
    ## When outputting get_room_info tool result
    Summarize the room information based SOLELY on the section "ข้อมูลย่อโดยรวมเกี่ยวกับห้อง" (General Summary). 
    - Provide a brief, warm, and inviting summary in Thai.
    - DO NOT include raw data from other sections unless specifically asked.
    """.format(current_date=datetime.now().strftime('%Y-%m-%d'))
    )
    
    response = model_with_tools.invoke([system_prompt] + state["messages"])
    
    return {
        "messages": [response],
    }



def route_tools(state: AgentGlobalState):
    """Custom routing: If tool calls, go to tools. Else go to renderer."""
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state: {state}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
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
