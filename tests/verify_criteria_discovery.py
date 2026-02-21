import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agent.booking.criteria_discovery.node import criteria_discovery_node
from agent.types import GlobalState, CriteriaDiscoveryState
from langchain_core.messages import HumanMessage

def test_extraction(user_message):
    print(f"\n--- Testing: {user_message} ---")
    state: GlobalState = {
        "messages": [HumanMessage(content=user_message)],
        "criteria_discovery_state": CriteriaDiscoveryState(),
        "intent": "start_booking",
        "phase": "criteria_discovery"
    }
    
    result = criteria_discovery_node(state)
    
    if isinstance(result, dict):
        print("Result (dict):", result.get("criteria_discovery_state").model_dump())
        if "messages" in result:
             print("Admin Question:", result["messages"][-1].content)
    else:
        print("Result (Command):", result.update.get("criteria_discovery_state").model_dump())
        print("Goto:", result.goto)

if __name__ == "__main__":
    test_cases = [
        "จอง 26 กุมภา 1 คืนครับ 2 ท่าน", # Exact
        "ไปวันที่ 10 พฤษภา กลับวันที่ 12 ค่ะ", # Exact
        "อยากจองพัก 2 คืน ช่วงวันที่ 10-15 พฤษภาค่ะ", # Flexible
        "สอบถามราคาที่พัก ช่วงมีนาค่ะ ยังไม่แน่ใจวันค่ะ", # Flexible (month)
        "S3, S4 ช่วง 4-8 มีนา ว่างวันไหนบ้างคะ" # Flexible with room numbers
    ]
    
    for tc in test_cases:
        test_extraction(tc)
