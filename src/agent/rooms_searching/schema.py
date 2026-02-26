from datetime import datetime
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass



@dataclass
class StayOption:
    is_split_stay: bool
    legs: List[StayLeg]
    total_price: float

@dataclass
class StayLeg:
    room_no: str
    room_type: str
    max_guests: int
    requested_guests: int
    from_to_dates: List[Tuple[str, str]]
    nightly_rates: Rates
    extra_bed_required: bool = False
    pricing: StayPricing

@dataclass
class PriceBreakdownItem:
    tier: str       # "Weekday" | "Weekend" | "Holiday"
    nights: int
    rate: float
    date: datetime
    subtotal: float

@dataclass
class ExtraBedInfo:
    nights: int
    rate: float = 700
    subtotal: float = 0

    def __post_init__(self):
        self.subtotal = self.nights * self.rate
@dataclass
class Rates:
    weekday: float
    weekend: float
    holiday: float

@dataclass
class StayPricing:
    total_price: float
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None