from agent.types import GlobalState, UserIntent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage


model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0
)


def intent_recognizer(state: GlobalState):
    """intent recognizer node identify user intent"""
    
    systemPrompt = SystemMessage(content="""
    You are the intent recognizer for AI chatbot agent of Tatoh Resort. 
    Your goal is to identify the user's intent.
    
    ## INTENTS:
    - 'greeting': User greeted the chatbot. 
    - 'start_booking': User wants to check room availability for specific dates.
    - 'asking_info': User is asking questions or requesting information about Tatoh Resort (e.g., room details, pictures, photos, prices, services, booking policies like cancellation or check-in) or Koh Tao island in general (e.g., weather, arrival guide, boat schedules, activities, travel advice).
    - 'out_of_scope': Anything completely unrelated to the resort, hospitality, tourism, or Koh Tao island (e.g., general world news, coding, cooking, politics, etc.).
    - 'adjust_criteria': User wants to adjust the room search criteria.
    - 'select_room': User selects a room after room searching (no payment made or confirmed yet).
    - 'confirm_booking_terms': User confirms booking terms, price and conditions.
    """)

    model_with_structured_output = model.with_structured_output(UserIntent)

    response = model_with_structured_output.invoke([systemPrompt] + state["messages"])

    parsed_intent = response.intent

    return {"intent": parsed_intent}