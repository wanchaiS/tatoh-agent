from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta

from agent.criteria_discovery.schema import Criteria
from agent.room_evaluation.tools.search_rooms import search_rooms, RoomCard


EXPANSION_STEPS = [0, 3, 5, 7]


@dataclass
class RunSearchResult:
    rooms: List[RoomCard]
    expanded_days: int
    exhausted: bool


def run_search(criteria: Criteria) -> RunSearchResult:
    """
    Search rooms with automatic window expansion.
    Returns rooms.
    """
    duration = criteria.duration_nights or 1
    
    # search_date_start/end is the single source of truth.
    # For exact mode, auto_fill() sets these from check_in/out.
    # For flexible mode, the user provides them directly.
    base_start_str = criteria.search_date_start
    base_end_str = criteria.search_date_end
    
    if not base_start_str or not base_end_str:
        return RunSearchResult(rooms=[], expanded_days=0, exhausted=True)
        
    start_dt = datetime.strptime(base_start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(base_end_str, "%Y-%m-%d")

    rooms = []
    
    for shift in EXPANSION_STEPS:
        curr_start = start_dt - timedelta(days=shift)
        curr_end = end_dt + timedelta(days=shift)
        
        rooms = search_rooms(
            guests=criteria.total_guests or 1,
            search_start=curr_start.strftime("%Y-%m-%d"),
            search_end=curr_end.strftime("%Y-%m-%d"),
            duration_nights=duration
        )
        
        if rooms:
            return RunSearchResult(rooms=rooms, expanded_days=shift, exhausted=False)

    return RunSearchResult(rooms=rooms, expanded_days=EXPANSION_STEPS[-1], exhausted=True)
