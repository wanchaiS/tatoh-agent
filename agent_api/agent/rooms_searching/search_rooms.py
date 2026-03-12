from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, TypedDict

from agent.criteria_discovery.schema import Criteria
from agent.rooms_searching.schema import AvailableDate, Rates, Room
from agent.services.room_availability import (
    RoomAvailabilityData,
    RoomAvailabilityService,
)
from agent.services.room_service import room_service
from agent.utils.pms_client import fetch_room_availability_window

EXPANSION_STEPS = [0, 3, 5, 7]


# ── Domain types ───────────────────────────────────────────────────────────────


@dataclass(slots=True)
class RoomCandidate:
    """Raw candidate room from PMS crossed with local Room metadata and computed comboss."""

    room_id: str
    room_no: str
    room_type_id: str
    room_type_name: str
    dates: List[str]
    price_weekdays: float
    price_weekends: float
    price_ny_songkran: float
    max_guests: int
    all_combos: List[List[str]] = None
    date_set: set = None


@dataclass
class RunSearchResult:
    rooms: List[Room]
    expanded_days: int
    exhausted: bool
    criteria_id: str


# ── Public entry point ─────────────────────────────────────────────────────────
async def search_rooms(criteria: Criteria) -> RunSearchResult:
    """
    Search rooms with automatic window expansion across multiple date windows.
    Returns rooms.
    """

    room_availability_service = RoomAvailabilityService()

    for shift in EXPANSION_STEPS:
        all_candidates = []

        # criteria.get_expanded_windows returns list of (start_str, end_str) tuples
        for window_start, window_end in criteria.get_expanded_windows(shift):
            candidates = await _search_rooms_window_candidates(
                availability_service=room_availability_service,
                search_start=window_start,
                search_end=window_end,
            )
            all_candidates.extend(candidates)

        if all_candidates:
            # Group all the raw candidates collected, merge their dates, and build valid combos
            rooms = _finalize_candidates(
                all_candidates,
                criteria.total_guests or 1,
                criteria.duration_nights or 1,
            )
            if rooms:
                return RunSearchResult(
                    rooms=rooms,
                    expanded_days=shift,
                    exhausted=False,
                    criteria_id=criteria.get_criteria_id(),
                )

    return RunSearchResult(
        rooms=[],
        expanded_days=EXPANSION_STEPS[-1],
        exhausted=True,
        criteria_id=criteria.get_criteria_id(),
    )


async def _search_rooms_window_candidates(
    availability_service: RoomAvailabilityService,
    search_start: str,
    search_end: str,
) -> List[RoomCandidate]:
    """
    Search available rooms within a given search window and return raw candidates.
    Only returns rooms that have consecutive availability for at least `duration_nights`.
    """
    search_start_dt = datetime.strptime(search_start, "%Y-%m-%d")
    search_end_dt = datetime.strptime(search_end, "%Y-%m-%d")

    # Tracker fetches dynamically and returns strictly clipped dates
    availability = availability_service.get_availability(search_start_dt, search_end_dt)
    room_metadata = await room_service.get_all_rooms()

    candidates = []

    for meta in room_metadata:
        room_no = meta.room_name.lower()
        raw = availability.get(room_no)
        if not raw:
            continue

        candidate = _build_candidate(raw, meta, room_no)
        candidates.append(candidate)

    return candidates


# ── Internal helpers ───────────────────────────────────────────────────────────


def _build_candidate(raw: RoomAvailabilityData, meta, room_no: str) -> RoomCandidate:
    """Merge PMS availability data with room metadata."""
    return RoomCandidate(
        room_id=raw["room_id"],
        room_no=room_no,
        room_type_id=raw["room_type_id"],
        room_type_name=raw["room_type_name"],
        dates=raw["dates"],
        price_weekdays=meta.price_weekdays,
        price_weekends=meta.price_weekends_holidays,
        price_ny_songkran=meta.price_ny_songkran,
        max_guests=meta.max_guests,
        all_combos=[],
        date_set=set(),
    )


def _finalize_candidates(
    candidates: List[RoomCandidate], guests: int, duration: int
) -> List[Room]:
    """Merge raw available dates for each room and build Room."""
    merged = _merge_candidates_by_room(candidates, duration)
    return [_to_room(c, guests) for c in merged]


def _to_room(room: RoomCandidate, guests: int) -> Room:
    extra_bed_req = guests > room.max_guests

    available_dates = []
    for combo in room.all_combos or []:
        if combo:
            available_dates.append(
                AvailableDate(start_date=combo[0], end_date=combo[-1])
            )

    return Room(
        room_no=room.room_no.upper(),
        room_type=room.room_type_name,
        max_guests=room.max_guests,
        available_dates=available_dates,
        nightly_rates=Rates(
            weekday=float(room.price_weekdays),
            weekend=float(room.price_weekends),
            holiday=float(room.price_ny_songkran),
        ),
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


def _merge_candidates_by_room(
    candidates: List[RoomCandidate], duration: int
) -> List[RoomCandidate]:
    """Merge raw dates for the exact same room across different search windows, then build valid combos."""
    merged: Dict[str, RoomCandidate] = {}

    for c in candidates:
        room_no = c.room_no
        if room_no not in merged:
            import copy

            merged[room_no] = copy.copy(c)
            merged[room_no].date_set = set(c.dates)
        else:
            merged[room_no].date_set.update(c.dates)

    # Calculate combinations on the merged raw dates
    result = []
    for item in merged.values():
        unique_dates = list(item.date_set)
        combos = _build_date_combos(unique_dates, duration)
        if combos:
            item.all_combos = combos
            result.append(item)

    return result
