from agent.types import GlobalState, UserIntent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
import json

model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0
)


def intent_recognizer(state: GlobalState):
    """intent recognizer node identify user intent"""
    
    # Ensure phase is a string, defaulting to "None" if missing or null
    current_phase = str(state.get("phase", "None"))

    relavant_context_map = {
        "criteria_discovery": state.get("criteria_discovery_state"),
    }

    relavant_context = relavant_context_map.get(current_phase, {})
    
    # Filter out any null-like or empty values
    info_to_show = {
        k: v for k, v in relavant_context.items() 
        if v is not None and v != ""
    }
    
    formatted_info = json.dumps(info_to_show, indent=2) if info_to_show else "No data collected yet"
    
    systemPrompt = SystemMessage(content=f"""
    You are the intent recognizer for AI chatbot agent of Tatoh Resort. 
    Your goal is to identify the user's intent based on the message and current context.
    
    ## CURRENT CONTEXT:
    - Current Phase: {current_phase}
    - Information Collected: 
    {formatted_info}

    ## INTENTS:
    - 'greeting': User greeted the chatbot. 
    - 'start_booking': User wants to check room availability or start a booking for specific dates.
    - 'asking_info': User is asking general, non-contextual facts about the resort or Koh Tao (e.g., Wi-Fi, check-in times, general pricing, weather, boat schedules, arrival guides).
    - 'evaluate_booking_options': User is asking for comparisons, recommendations, or specific qualitative details about options to help them decide (e.g., "Which room has a better view?", "Can I swap the tour for a kayak?", "Is S1 better than S5?").
    - 'out_of_scope': Anything completely unrelated to the resort, hospitality, or Koh Tao.
    - 'adjust_criteria': User wants to change dates, guest count, or room types in their current search.
    - 'select_room': User picks a specific room to proceed with (no payment yet).
    - 'confirm_booking_terms': User accepts the price/policy and is ready to pay or asks for bank details.

    ## EXAMPLES:
    - "มีกิจกรรมดำน้ำไหมคะ" -> 'asking_info'
    - "ระหว่างห้อง V2, S1, S2 ห้องไหนสวยสุดคะ" -> 'evaluate_booking_options'
    - "ห้องน้ำแต่ละห้องมีสายฉีดชำระไหมคะ" -> 'asking_info'
    - "ถ้าไม่เอาดำน้ำ สามารถเปลี่ยนเป็นเรือคายัคได้ไหมคะ" -> 'evaluate_booking_options'
    - "วันที่ 19-21 มีนา 4 ท่าน ราคาเท่าไหร่คะ" -> 'start_booking'
    - "จอง S1 ค่ะ" -> 'select_room'
    - "ขอเลขบัญชี ค่ะ" -> 'confirm_booking_terms'
    - "ขอเปลี่ยนเป็นวันที่ 4 เมษาค่ะ" -> 'adjust_criteria'
    - "เพิ่มอีกหนึ่งคืนได้ไหมค่ะ" -> 'adjust_criteria'
    """)

    model_with_structured_output = model.with_structured_output(UserIntent)

    response = model_with_structured_output.invoke([systemPrompt] + state["messages"])

    parsed_intent = response.intent

    return {"intent": parsed_intent}