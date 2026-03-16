from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AvailableDate(BaseModel):
    start_date: str = Field(
        ..., description="Start of the available date (YYYY-MM-DD)."
    )
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

    # Enriched fields (populated from room metadata)
    room_id: int | None = None
    room_name: str | None = None
    summary: str | None = None
    bed_queen: int | None = None
    bed_single: int | None = None
    baths: int | None = None
    size: float | None = None
    price_weekdays: float | None = None
    price_weekends_holidays: float | None = None
    price_ny_songkran: float | None = None
    steps_to_beach: int | None = None
    steps_to_restaurant: int | None = None
    sea_view: int | None = None
    privacy: int | None = None
    room_design: int | None = None
    room_newness: int | None = None
    tags: list[str] | None = None
    thumbnail_url: str | None = None


class RoomSearchResult(BaseModel):
    rooms: List[Room]
    criteria_id: str
    expanded_days: int
    exhausted: bool
    search_results_summary: str


class PriceBreakdownItem(BaseModel):
    tier: str
    nights: int
    rate: float
    subtotal: float


class ExtraBedInfo(BaseModel):
    nights: int
    rate_per_night: float = 500.0
    subtotal: float = 0.0

    def model_post_init(self, __context):
        if self.subtotal == 0:
            object.__setattr__(self, "subtotal", self.nights * self.rate_per_night)


class StayPricing(BaseModel):
    total_price: float
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None
