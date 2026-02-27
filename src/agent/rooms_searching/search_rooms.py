import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from agent.utils.pms_client import get_room_availability
from agent.utils.google_drive_client import read_spreadsheet_data
from agent.utils.date_utils import format_date_ranges

from agent.criteria_discovery.schema import Criteria
from agent.rooms_searching.schema import StayOption

# Cache room metadata — read_spreadsheet_data takes ~4s, no need to call it on every search
_METADATA_TTL = 600  # 10 minutes
EXPANSION_STEPS = [0, 3, 5, 7]


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
class RoomCard:
    room_no: str
    room_type: str
    max_guests: int
    requested_guests: int 
    available_ranges: List[str]
    nightly_rates: Dict[str, int]
    extra_bed_required: bool = False

@dataclass
class RunSearchResult:
    rooms: List[RoomCard]
    expanded_days: int
    exhausted: bool
    criteria_id: str

# ── Public entry point ─────────────────────────────────────────────────────────

# TODO: Async Migration - Once `pms_client.get_room_availability` is converted to an `async def`,
# this core `search_rooms` orchestration loop should also become `async def` and `await` the PMS client.
def search_rooms(criteria: Criteria) -> RunSearchResult:
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
        return RunSearchResult(rooms=[], expanded_days=0, exhausted=True, criteria_id=criteria.get_criteria_id())
        
    start_dt = datetime.strptime(base_start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(base_end_str, "%Y-%m-%d")

    rooms = []
    
    for shift in EXPANSION_STEPS:
        curr_start = start_dt - timedelta(days=shift)
        curr_end = end_dt + timedelta(days=shift)
        
        rooms = _search_rooms_window(
            guests=criteria.total_guests or 1,
            search_start=curr_start.strftime("%Y-%m-%d"),
            search_end=curr_end.strftime("%Y-%m-%d"),
            duration_nights=duration
        )
        
        if rooms:
            return RunSearchResult(rooms=rooms, expanded_days=shift, exhausted=False, criteria_id=criteria.get_criteria_id())

    return RunSearchResult(rooms=rooms, expanded_days=EXPANSION_STEPS[-1], exhausted=True, criteria_id=criteria.get_criteria_id())

def _search_rooms_window(
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

# ── Internal helpers ───────────────────────────────────────────────────────────

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
