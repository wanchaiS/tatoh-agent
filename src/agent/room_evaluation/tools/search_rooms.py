import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from utils.pms_client import get_room_availability
from utils.google_drive_client import read_spreadsheet_data
from utils.date_utils import format_date_ranges

# Cache room metadata — read_spreadsheet_data takes ~4s, no need to call it on every search
_METADATA_TTL = 600  # 10 minutes

_room_metadata: list | None = None
_room_metadata_expires_at: float = 0

def _get_room_metadata() -> list:
    global _room_metadata, _room_metadata_expires_at
    if _room_metadata is None or time.time() > _room_metadata_expires_at:
        _room_metadata = read_spreadsheet_data("/cooper-project/data/rooms_info")
        _room_metadata_expires_at = time.time() + _METADATA_TTL
    return _room_metadata


# ── Domain types ───────────────────────────────────────────────────────────────

@dataclass
class PriceBreakdownItem:
    tier: str       # "Weekday" | "Weekend" | "Holiday"
    nights: int
    rate: int
    subtotal: int

@dataclass
class ExtraBedInfo:
    nights: int
    rate: int = 700
    subtotal: int = 0

    def __post_init__(self):
        self.subtotal = self.nights * self.rate

@dataclass
class StayPricing:
    total_price: int
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None

@dataclass
class RoomCard:
    room_no: str
    room_type: str
    max_guests: int
    requested_guests: int
    available_ranges: List[str]
    nightly_rates: Dict[str, int]
    extra_bed_required: bool = False
    # Populated by calculate_stay_pricing() when exact dates are known
    pricing: Optional[StayPricing] = None


# ── Public entry point ─────────────────────────────────────────────────────────

def search_rooms(
    guests: int,
    search_start: str,
    search_end: str,
    duration_nights: int = 1,
) -> List[RoomCard]:
    """
    Search available rooms within a given search window.
    Only returns rooms that have consecutive availability for at least `duration_nights`.
    """
    search_start_dt = datetime.strptime(search_start, "%Y-%m-%d")
    search_end_dt = datetime.strptime(search_end, "%Y-%m-%d")

    # PMS client is clipped strictly returning valid dates in [search_start, search_end)
    availability = get_room_availability(search_start_dt, search_end_dt).get("rooms", {})
    room_metadata = _get_room_metadata()

    candidates = []

    for meta in room_metadata:
        room_no = meta["room_name"].lower()
        raw = availability.get(room_no)
        if not raw:
            continue

        candidate = _build_candidate(raw, meta, room_no)
        candidate["all_combos"] = _build_date_combos(candidate["dates"], duration_nights)

        if candidate["all_combos"]:
            candidates.append(candidate)

    return _finalize_candidates(candidates, guests)


# ── Pipeline steps ─────────────────────────────────────────────────────────────

def _build_candidate(raw: dict, meta: dict, room_no: str) -> dict:
    """Merge PMS availability data with room metadata."""
    return {
        **raw,
        "room_no": room_no,
        "price_weekdays": meta["price_weekdays"],
        "price_weekends": meta["price_weekends_holidays"],
        "price_ny_songkran": meta["price_ny_songkran"],
        "max_guests": int(meta["max_guests"]),
    }


def _finalize_candidates(candidates: list, guests: int) -> List[RoomCard]:
    """Group and attach available date ranges for rooms."""
    grouped = _group_by_type_and_dates(candidates)
    return [_to_room_card(c, guests) for c in grouped]


def _to_room_card(room: dict, guests: int) -> RoomCard:
    extra_bed_req = guests > room.get("max_guests", 0)
    return RoomCard(
        room_no=room.get("room_no", "N/A").upper(),
        room_type=room.get("room_type_name", "Unknown"),
        max_guests=room.get("max_guests", 0),
        requested_guests=guests,
        available_ranges=format_date_ranges(room["all_combos"]),
        nightly_rates={
            "weekday": int(room.get("price_weekdays", 0)),
            "weekend": int(room.get("price_weekends", 0)),
            "holiday": int(room.get("price_ny_songkran", 0)),
        },
        extra_bed_required=extra_bed_req,
    )


# ── Availability helpers ───────────────────────────────────────────────────────

def _build_date_combos(dates: list, duration: int) -> List[List[str]]:
    """Find all consecutive date sequences that cover the required duration."""
    if not dates:
        return []
    sorted_dts = sorted(datetime.strptime(d, "%Y-%m-%d") for d in dates)
    combos, current = [], []
    for i, dt in enumerate(sorted_dts):
        if not current or (dt - sorted_dts[i - 1]).days == 1:
            current.append(dt.strftime("%Y-%m-%d"))
        else:
            if len(current) >= duration:
                combos.append(current)
            current = [dt.strftime("%Y-%m-%d")]
    if len(current) >= duration:
        combos.append(current)
    return combos


# ── Grouping ───────────────────────────────────────────────────────────────────

def _group_by_type_and_dates(candidates: list) -> list:
    """Merge rooms of the same type with identical availability into one card."""
    grouped: Dict[tuple, dict] = {}
    for c in candidates:
        key = (c["room_type_id"], tuple(tuple(combo) for combo in c["all_combos"]))
        if key not in grouped:
            grouped[key] = {**c, "room_nos": [c["room_no"]]}
        else:
            grouped[key]["room_nos"].append(c["room_no"])

    result = []
    for item in grouped.values():
        item["room_no"] = ", ".join(sorted(item["room_nos"]))
        result.append(item)
    return result


# ── Pricing ────────────────────────────────────────────────────────────────────

_HOLIDAYS = lambda dt: (
    (dt.month == 12 and dt.day >= 25) or
    (dt.month == 1 and dt.day <= 5) or
    (dt.month == 4 and 10 <= dt.day <= 17)
)
_WEEKENDS = lambda dt: dt.weekday() in [4, 5, 6]


def calculate_stay_pricing(
    card: RoomCard,
    check_in: str,
    check_out: str,
) -> RoomCard:
    """
    Calculate exact pricing for a RoomCard given specific check-in/out dates.
    Mutates and returns the card with pricing populated.
    """
    check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    rates = card.nightly_rates
    rate_map = {
        "Weekday": rates.get("weekday", 0),
        "Weekend": rates.get("weekend", 0),
        "Holiday": rates.get("holiday", 0),
    }
    counts = {"Weekday": 0, "Weekend": 0, "Holiday": 0}

    current = check_in_dt
    while current < check_out_dt:
        tier = "Holiday" if _HOLIDAYS(current) else "Weekend" if _WEEKENDS(current) else "Weekday"
        counts[tier] += 1
        current += timedelta(days=1)

    total = sum(rate_map[t] * counts[t] for t in counts)
    breakdown = [
        PriceBreakdownItem(tier=t, nights=counts[t], rate=rate_map[t], subtotal=counts[t] * rate_map[t])
        for t in counts if counts[t] > 0
    ]

    extra_bed = None
    if card.extra_bed_required:
        num_nights = (check_out_dt - check_in_dt).days
        extra_bed = ExtraBedInfo(nights=num_nights)
        total += extra_bed.subtotal

    card.pricing = StayPricing(total_price=total, breakdown=breakdown, extra_bed=extra_bed)
    return card
