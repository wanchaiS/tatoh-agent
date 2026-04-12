from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel

from agent.services.room_schemas import Rates


class PriceBreakdownItem(BaseModel):
    tier: str
    nights: int
    rate: float
    subtotal: float


class ExtraBedInfo(BaseModel):
    nights: int
    rate_per_night: float = 700.0
    subtotal: float = 0.0

    def model_post_init(self, __context):
        if self.subtotal == 0:
            object.__setattr__(self, "subtotal", self.nights * self.rate_per_night)


class StayPricing(BaseModel):
    total_price: float
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None


class PricingSummary(BaseModel):
    total_price: float
    breakdown_text: str
    extra_bed_note: Optional[str] = None

_HOLIDAYS = lambda dt: (
    (dt.month == 12 and dt.day >= 25)
    or (dt.month == 1 and dt.day <= 5)
    or (dt.month == 4 and 10 <= dt.day <= 17)
)
_WEEKENDS = lambda dt: dt.weekday() in [4, 5, 6]


def calculate_stay_pricing(
    check_in: str,
    check_out: str,
    rates: Rates,
    extra_bed_required: bool = False,
) -> StayPricing:
    """
    Calculate exact pricing for given rates and check-in/out dates.
    """
    check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    rate_map = {
        "Weekday": rates.weekday,
        "Weekend": rates.weekend,
        "Holiday": rates.holiday,
    }
    counts = {"Weekday": 0, "Weekend": 0, "Holiday": 0}

    current = check_in_dt
    while current < check_out_dt:
        tier = (
            "Holiday"
            if _HOLIDAYS(current)
            else "Weekend"
            if _WEEKENDS(current)
            else "Weekday"
        )
        counts[tier] += 1
        current += timedelta(days=1)

    total = sum(rate_map[t] * counts[t] for t in counts)
    breakdown = [
        PriceBreakdownItem(
            tier=t, nights=counts[t], rate=rate_map[t], subtotal=counts[t] * rate_map[t]
        )
        for t in counts
        if counts[t] > 0
    ]

    extra_bed = None
    if extra_bed_required:
        num_nights = (check_out_dt - check_in_dt).days
        extra_bed = ExtraBedInfo(nights=num_nights)
        total += extra_bed.subtotal

    return StayPricing(total_price=total, breakdown=breakdown, extra_bed=extra_bed)
