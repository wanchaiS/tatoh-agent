from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage 
from utils.language import is_thai

from agent.types import GlobalState
from agent.chat.chat_graph import chat_graph
from agent.booking.booking_graph import booking_graph
from agent.intent_recognizer import intent_recognizer


def router(state: GlobalState):
    intent = state.get("intent")

    intent_map = {
        "greeting": "chat_graph",
        "asking_info": "chat_graph",
        "out_of_scope": "out_of_scope_node",
        "start_booking": "booking_graph",
        "adjust_criteria": "booking_graph",
        "select_room": "booking_graph",
        "confirm_booking_terms": "booking_graph"
    }

    return intent_map.get(intent, "chat_graph")


def out_of_scope_node(state: GlobalState):
    """handle out of scope messages"""

    # Safer retrieval of the last human message
    human_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    last_msg_content = human_messages[-1].content if human_messages else ""

    language = "Thai" if is_thai(last_msg_content) else "English"

    if language == "Thai":
        response = "ขอโทษครับ ผมสามารถตอบได้เพียงข้อมูลเกี่ยวกับเกาะเต่า ตาโต๊ะรีสอร์ท หรือช่วยเรื่องการจองห้องพักเท่านั้นครับ"
    else:
        response = "I'm sorry, I can only answer questions about Koh Tao and Tatoh Resort, or help with bookings."
    return {"messages": [AIMessage(content=response)]}

graph_builder = StateGraph(GlobalState)

# 1. Add Nodes
graph_builder.add_node("intent_recognizer", intent_recognizer)
graph_builder.add_node("chat_graph", chat_graph)
graph_builder.add_node("booking_graph", booking_graph)
graph_builder.add_node("out_of_scope_node", out_of_scope_node)

# 2. Define Edges

graph_builder.add_edge(START, "intent_recognizer")
graph_builder.add_conditional_edges("intent_recognizer", router, {
        "chat_graph": "chat_graph",
        "booking_graph": "booking_graph",
        "out_of_scope_node": "out_of_scope_node"
    })

# After sub-graphs finish, they go to END
graph_builder.add_edge("chat_graph", END)
graph_builder.add_edge("booking_graph", END)
graph_builder.add_edge("out_of_scope_node", END)

graph = graph_builder.compile()
