from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class AvailableDate(BaseModel):
    start_date: str = Field(..., description="Start of the available date (YYYY-MM-DD).")
    end_date: str = Field(..., description="End of the available date (YYYY-MM-DD).")

    def window_days(self) -> int:
        """Total span of this window in days."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        return (end - start).days

class Rates(BaseModel):
    weekday: float
    weekend: float
    holiday: float

class Room(BaseModel):
    room_no: str
    room_type: str
    max_guests: int
    available_dates: List[AvailableDate]
    nightly_rates: Rates
    extra_bed_required: bool = False

class RoomSearchResult(BaseModel):
    rooms: List[Room]
    criteria_id: str
    expanded_days: int
    exhausted: bool
    search_results_summary: str


