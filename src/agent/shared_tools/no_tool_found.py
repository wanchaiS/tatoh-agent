from langchain.tools import tool

@tool
def no_tool_found() -> str:
    """
    Call this tool when a user asks a question about Tatoh Resort's services, facilities, 
    rooms, or policies, but you cannot find a specific tool to answer it.
    DO NOT guess or use your pre-trained knowledge to answer resort-specific questions.
    """
    return "ขอโทษนะคะ ตอนนี้คูเปอร์ยังไม่ถูกเทรนให้ตอบคำถามเกี่ยวกับเรื่องนี้ได้ รบกวนสอบถามพนักงานอีกครั้งนะคะ"
