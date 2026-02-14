from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from typing import  Optional,Dict,Any
import json
from langgraph.graph import StateGraph, START,MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from agent.types import GlobalState
from agent.chat.tools.find_boat_schedules import find_boat_schedules
from agent.chat.tools.get_gopro_service_info import get_gopro_service_info
from agent.chat.tools.get_kohtao_arrival_guide import get_kohtao_arrival_guide
from agent.chat.tools.get_kohtao_current_weather import get_kohtao_current_weather
from agent.chat.tools.get_kohtao_general_season import get_kohtao_general_season
from agent.chat.tools.get_room_gallery import get_room_gallery
from agent.chat.tools.get_room_info import get_room_info
from agent.chat.tools.no_tool_found import no_tool_found
from agent.chat.tools.ask_for_clarification import ask_for_clarification



class ChatState(MessagesState):
    """ Chat agent private state, keep the global clean"""
    booking_context: Optional[Dict[str, Any]]

qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
    no_tool_found,
    ask_for_clarification
]

tool_node = ToolNode(qa_tools, handle_tool_errors=True)

model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0
)

model_with_tools = model.bind_tools(qa_tools)

def chat_agent_node(state: ChatState) -> str:
    """
        Chat agent that answers all the questions.
    """

    context = state.get("booking_context")
    formatted_context = json.dumps(context, indent=2)

    systemPrompt = SystemMessage(content=f"""
        You are the Tatoh Resort chat agent that handles questions users may have.
        
        ## RULES:
        - If user's you are not sure about arguments for a tool, ask user to clarify or confirm the arguments.
        - NEVER use your pre-trained knowledge to answer questions about Tatoh Resort's specific services, facilities, rooms, or prices. ONLY use the provided tools.
        - If the user asks about a resort service, facility, room, or price and NO tool is found to answer it, you MUST call the `no_tool_found` tool.
        - If questions are regarding Kohtao island in general (not specific to our resort), you can answer with your general knowledge.
        - If the query is not clear or you need more information to proceed, call tool `ask_for_clarification`.

        ## TONES:
        - Answer in the same language as user.
        - Keep it short, concise, no markup format, natural sentence as human.

        ## CONTEXT:
        {formatted_context}
    """)

    # Pass global messages to chat agent for context understanding
    messages = [systemPrompt] + state["messages"]

    # Run the chat agent
    response = model_with_tools.invoke(messages)

    return {"messages": [response]}

chat_agent_builder = StateGraph(ChatState)
chat_agent_builder.add_node("chat_agent", chat_agent_node)
chat_agent_builder.add_node("tools", tool_node)

chat_agent_builder.add_edge(START, "chat_agent")
chat_agent_builder.add_conditional_edges("chat_agent", tools_condition)
chat_agent_builder.add_edge("tools", "chat_agent")

chat_agent_graph = chat_agent_builder.compile()

def chat_graph(state: GlobalState):
    """Chat entry node"""
    inputs = {"messages": state["messages"], "booking_context": state.get("booking_context",{})}

    result = chat_agent_graph.invoke(inputs)

    return {"messages": [result["messages"][-1]]}