from typing import Optional, Dict, Any
from pydantic import BaseModel

class RoomEvaluationState(BaseModel):
    current_criteria_id: Optional[str] = None
    current_search_results: Optional[Dict[str, Any]] = None
    window_extension_count: int = 0