import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# Add src to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(root_path / ".env")
except ImportError:
    pass

from agent.intent_recognizer import intent_recognizer

def test_intent(messages):
    print(f"--- Testing Intent Recognition ---")
    state = {"messages": messages}
    result = intent_recognizer(state)
    print(f"Detected Intent: {result.get('intent')}")
    print(f"----------------------------------")

if __name__ == "__main__":
    # Simulate the conversation from the screenshot
    messages = [
        HumanMessage(content="ขอข้อมูลห้อง S1 หน่อย"),
        AIMessage(content="ห้องพัก: S1 (Family Sea View Bungalow)\nรายละเอียด: ..."),
        HumanMessage(content="ขอดูรูปได้ไหม")
    ]
    
    test_intent(messages)
    
    # Also test with English
    messages_en = [
        HumanMessage(content="Show me room S1"),
        AIMessage(content="Room S1 is a Family Sea View Bungalow..."),
        HumanMessage(content="Can I see pictures?")
    ]
    test_intent(messages_en)
