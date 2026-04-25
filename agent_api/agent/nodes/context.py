from typing import Any

from langgraph.runtime import Runtime

from agent.context.agent_service_provider import AgentServiceProvider
from agent.state import State
from agent.types import InternalRoom
from db.models import Room


async def context_node(
    state: State, runtime: Runtime[AgentServiceProvider]
) -> dict[str, dict[str, InternalRoom]]:
    """Context that can be re-used in the graph, to avoid re-fetching data from the database."""
    room_service = runtime.context.room_service
    rooms: list[Room] = await room_service.get_all_rooms()
    room_ids = [room.id for room in rooms]
    all_photos = await room_service.get_all_photos_for_rooms(room_ids=room_ids)

    internal_room_dict: dict[str, InternalRoom] = {}
    for room in rooms:
        photos = all_photos.get(room.id, [])
        thumbnail_url = photos[0]["thumbnails"][240] if photos else ""
        internal_room_dict[room.room_name.lower()] = InternalRoom(
            id=room.id,
            room_name=room.room_name,
            room_type=room.room_type,
            summary=room.summary,
            bed_queen=room.bed_queen,
            bed_single=room.bed_single,
            baths=room.baths,
            size=room.size,
            price_weekdays=room.price_weekdays,
            price_weekends_holidays=room.price_weekends_holidays,
            price_ny_songkran=room.price_ny_songkran,
            max_guests=room.max_guests,
            steps_to_beach=room.steps_to_beach,
            sea_view=room.sea_view,
            privacy=room.privacy,
            steps_to_restaurant=room.steps_to_restaurant,
            room_design=room.room_design,
            room_newness=room.room_newness,
            tags=room.tags.split(",") if room.tags else [],
            thumbnail_url=thumbnail_url,
            photos=photos,
        )
    return {"rooms": internal_room_dict}
