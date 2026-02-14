from langchain.tools import tool

@tool
def no_tool_found() -> str:
    """
    Call this tool when a user asks a question about Tatoh Resort's services, facilities, 
    rooms, or policies, but you cannot find a specific tool to answer it.
    DO NOT guess or use your pre-trained knowledge to answer resort-specific questions.
    """
    return "I'm sorry, I don't have specific information about that service or facility at Tatoh Resort right now. Please ask about boat schedules, weather, GoPro rentals, or specific room details, or wait for a human agent to assist you."
