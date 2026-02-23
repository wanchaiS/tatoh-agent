from typing import Optional, List
from pydantic import BaseModel
from agent.rooms_searching.search_rooms import RoomCard

class RoomEvaluationState(BaseModel):
    current_criteria_id: Optional[str] = None
    current_search_results: Optional[List[RoomCard]] = None
    search_results_summary: Optional[str] = None
    expanded_days: int = 0
    exhausted: bool = False
    guest_meta_data: Optional[str] = None
    selected_room_no: Optional[str] = None