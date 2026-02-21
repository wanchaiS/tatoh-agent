from typing import Annotated, Literal, Optional, Any
from pydantic import BaseModel
from langgraph.graph import MessagesState

from agent.criteria_discovery.schema import Criteria
from agent.room_evaluation.schema import RoomEvaluationState

def update_room_evaluation_state(left: Optional[RoomEvaluationState], right: Optional[Any]) -> RoomEvaluationState:
    """merge new room evaluation state into existing state"""
    if left is None:
        left = RoomEvaluationState()
    if right is None:
        return left
    
    # Handle dict updates or full model updates
    new_data = right if isinstance(right, dict) else right.model_dump(exclude_unset=True)
    
    # Merge values into the current model
    current_data = left.model_dump()
    current_data.update(new_data)
    
    return RoomEvaluationState.model_validate(current_data)

def update_criteria(left: Optional[Criteria], right: Optional[Any]) -> Criteria:
    """merge new criteria discovery state into existing state"""
    if left is None:
        left = Criteria()
    if right is None:
        return left
    
    # Handle dict updates or full model updates
    new_data = right if isinstance(right, dict) else right.model_dump(exclude_unset=True)
    
    # Merge values into the current model
    current_data = left.model_dump()
    current_data.update(new_data)
    
    return Criteria.model_validate(current_data)

Phase = Literal["criteria_discovery",
                  "evaluate_options",
                  "payment_settlement",
                  "contact_info_collection",
                  "summarize_booking"]

class GlobalState(MessagesState):
    phase: Phase
    criteria: Annotated[Criteria, update_criteria]
    room_evaluation_state: Annotated[RoomEvaluationState, update_room_evaluation_state]
