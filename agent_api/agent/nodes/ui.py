import uuid
from datetime import date, timedelta
from typing import Any

from langgraph.graph.ui import push_ui_message

from agent.state import State
from agent.types import MAP_SRC, ROOM_PIN_POSITIONS, RoomCard


def push_pending_search_results_ui_node(state: State) -> dict[str, Any] | None:
    pending_search_results = state["pending_render_search_results"]
    if not pending_search_results:
        return None

    # merge rooms
    merged = {}
    for result_dict in pending_search_results:
        for room_name, dates in result_dict.items():
            if room_name not in merged:
                merged[room_name] = set(dates)
            else:
                merged[room_name].update(set(dates))

    # populate room cards
    room_cards: list[RoomCard] = []
    for room_name, dates in merged.items():
        room = state["rooms"][room_name]
        room_cards.append(
            {
                "id": room["id"],
                "room_name": room["room_name"],
                "room_type": room["room_type"],
                "summary": room["summary"],
                "bed_queen": room["bed_queen"],
                "bed_single": room["bed_single"],
                "baths": room["baths"],
                "size": room["size"],
                "price_weekdays": room["price_weekdays"],
                "price_weekends_holidays": room["price_weekends_holidays"],
                "price_ny_songkran": room["price_ny_songkran"],
                "max_guests": room["max_guests"],
                "steps_to_beach": room["steps_to_beach"],
                "sea_view": room["sea_view"],
                "privacy": room["privacy"],
                "steps_to_restaurant": room["steps_to_restaurant"],
                "room_design": room["room_design"],
                "room_newness": room["room_newness"],
                "tags": room["tags"],
                "thumbnail_url": room["thumbnail_url"],
                "photos": room["photos"],
                "date_ranges": dates_to_ranges(dates),
            }
        )

    map_data = {
        "src": MAP_SRC,
        "pins": ROOM_PIN_POSITIONS,
    }
    search_range = state.get("pending_search_range") or {}

    last_ai_message = state["messages"][-1]

    push_ui_message(
        name="search_results",
        props={"rooms": room_cards, "map": map_data, "search_range": search_range},
        id=str(uuid.uuid4()),
        message=last_ai_message,
    )

    return {
        "pending_render_search_results": "clear",
        "pending_search_range": None,
    }


def dates_to_ranges(dates: set[str]) -> list[dict[str, str]]:
    if not dates:
        return []
    sorted_dates = sorted(dates)
    ranges: list[dict[str, str]] = []
    start = end = sorted_dates[0]
    for d in sorted_dates[1:]:
        end_next = date.fromisoformat(end) + timedelta(days=1)
        if date.fromisoformat(d) == end_next:
            end = d
        else:
            ranges.append({"start": start, "end": end})
            start = end = d
    ranges.append({"start": start, "end": end})
    return ranges
