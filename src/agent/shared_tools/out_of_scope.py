from langchain.tools import tool

@tool
def out_of_scope() -> str:
    """
    Call this when the user asks about something completely unrelated to Tatoh Resort, 
    Koh Tao, or their booking.
    """
    return "คูเปอร์ตอบได้เฉพาะเรื่องที่เกี่ยวกับเกาะเต่าและตาโต๊ะรีสอร์ทเท่านั้นค่ะ"