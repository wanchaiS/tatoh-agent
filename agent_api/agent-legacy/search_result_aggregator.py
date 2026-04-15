import uuid

from agent.search_phase.tools.search_available_rooms import (
    ToolRoomSearchResult,
    build_date_ranges,
)
from agent.services.room_schemas import Rates, RoomAvailability, RoomCard

from agent.services.room_service import room_service
from agent.types import GlobalState


async def search_result_aggregator(state: GlobalState) -> dict:
    """Aggregate raw search results into merged RoomCards + UI.

    Runs after every ToolNode execution. Only acts when search_results_pending
    is True (set by agent_node when a search tool call is detected).
    """
    if not state.get("search_results_pending"):
        return {}

    raw_results: list[ToolRoomSearchResult] = state.get("tool_room_search_results") or []
    if not raw_results:
        return {"search_results_pending": False}

    # 1. Merge rooms across windows — union dates by room_name
    merged: dict[str, list[str]] = {}  # room_name (lower) → all dates
    duration = raw_results[0].duration_nights
    for sr in raw_results:
        for room_name, dates in sr.rooms.items():
            key = room_name.lower()
            if key not in merged:
                merged[key] = []
            merged[key].extend(dates)

    # Deduplicate dates
    for key in merged:
        merged[key] = list(set(merged[key]))

    # 2. Fetch room info from DB
    db_rooms = await room_service.get_all_rooms()
    db_by_name = {r.room_name.lower(): r for r in db_rooms}

    # 3. Build RoomCards with DateRanges
    room_cards: list[RoomCard] = []
    for room_name_lower, dates in merged.items():
        db_room = db_by_name.get(room_name_lower)
        if not db_room:
            continue
        date_ranges = build_date_ranges(dates, duration)
        card = RoomCard.from_db(db_room)
        card.availability = RoomAvailability(
            dates=dates,
            date_ranges=date_ranges,
            nightly_rates=Rates(
                weekday=db_room.price_weekdays,
                weekend=db_room.price_weekends_holidays,
                holiday=db_room.price_ny_songkran,
            ),
        )
        room_cards.append(card)

    # 4. Attach thumbnails
    if room_cards:
        room_ids = [c.id for c in room_cards]
        thumb_map = await room_service.get_first_photo_urls(room_ids)
        for card in room_cards:
            card.thumbnail_url = thumb_map.get(card.id)

    # 5. Build UI
    pending_ui = [{
        "name": "search_results",
        "props": {"rooms": [r.model_dump() for r in room_cards]},
        "id": str(uuid.uuid4()),
    }]

    return {
        "search_results_pending": False,
        "aggregated_room_search_results": room_cards,
        "pending_ui": pending_ui,
    }
