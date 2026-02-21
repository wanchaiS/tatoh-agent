from langchain.tools import tool

@tool
def ask_for_clarification(question: str) -> str:
    """
    Call this tool when the user's request is unclear, ambiguous, or lacks sufficient information 
    to be handled by other tools.
    provide the 'question' to ask the user to clarify their intent.
    """
    return question
