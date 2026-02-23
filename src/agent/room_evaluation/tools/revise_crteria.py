from langchain_core.tools import tool

@tool
def revise_criteria():
    """
    Call this tool ONLY when the user explicitly requests to change their core booking parameters. 
    This includes changing check-in or check-out dates, modifying the number of guests, or changing 
    the duration of their stay (e.g., 'ขอเปลี่ยนเป็นไป 3 คนค่ะ', 'เลื่อนเป็นเดือนหน้าได้ไหม', 'เพิ่มเป็น 2 คืน'). 
    
    Calling this tool signals the system to discard the current room search results and start a new search. 
    DO NOT call this if the user is just asking about room features or confirming a room.
    """
    # TODO: implement
    pass
    