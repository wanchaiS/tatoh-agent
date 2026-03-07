from typing import Optional, List
from pydantic import BaseModel

class RoomEvaluationState(BaseModel):
    guest_meta_data: Optional[str] = None
    selected_room_no: Optional[str] = None