from langchain_core.messages import AIMessage
from agent.types import GlobalState

def finalizing_booking_node(state: GlobalState):
    return {"messages": [AIMessage(content="Please review the booking terms and confirm to proceed to payment.")]}

def payment_settlement_node(state: GlobalState):
    return {"messages": [AIMessage(content="Please transfer the deposit to our Krungsri Bank account and send the slip here.")]}

def contact_info_collection_node(state: GlobalState):
    return {"messages": [AIMessage(content="Thank you! Please provide your full name and phone number for the reservation system.")]}

def summarize_booking_node(state: GlobalState):
    return {"messages": [AIMessage(content="All set! Here is your booking summary and confirmation voucher.")]}
