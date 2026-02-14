from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
from pydantic import BaseModel
from langgraph.graph import MessagesState


class BookingContext(TypedDict):
    check_in_date: Optional[str]
    check_out_date: Optional[str]
    total_guests: Optional[int]
    room_split_strategy: Optional[list[int]]
    duration_nights: Optional[int]
    search_date_start: Optional[str]
    search_date_end: Optional[str]
    preferred_room_no: Optional[str]
    preferred_room_type: Optional[str]
    phase: str

Intent = Literal["greeting",
                 "start_booking",
                 "asking_info",
                 "out_of_scope",
                 "adjust_criteria",
                 "select_room",
                 "confirm_booking_terms"]

class UserIntent(BaseModel):
    intent: Intent

def update_booking_context(left: BookingContext, right: Optional[dict]) -> BookingContext:
    """merge new context into existing context"""
    if not left:
        left = {
            "phase": "discovering",
            "check_in_date": None,
            "check_out_date": None,
            "total_guests": None,
            "room_split_strategy": None,
            "duration_nights": None,
            "search_date_start": None,
            "search_date_end": None,
            "preferred_room_no": None,
            "preferred_room_type": None,
        }
    
    if not right: 
        return left
        
    return {**left, **right}

class GlobalState(MessagesState):
    booking_context: Annotated[BookingContext, update_booking_context]
    intent: Intent
