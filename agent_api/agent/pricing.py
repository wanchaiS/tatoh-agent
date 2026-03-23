from datetime import datetime, timedelta

from agent.schemas import (
    ExtraBedInfo,
    PriceBreakdownItem,
    Rates,
    StayPricing,
)

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
