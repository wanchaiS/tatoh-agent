from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Set, Tuple
from typing_extensions import TypedDict

from agent.utils.pms_client import PmsRoomAvailability

if TYPE_CHECKING:
    from agent.utils.pms_client import PmsClient


class InternalRoomAvailabilityData(TypedDict):
    """Internal cache representation — dates kept as a set for efficient merge/discard."""
    room_id: str          # PMS internal room ID
    room_no: str          # Room number, lowercased (e.g. "s5")
    room_type_id: str     # PMS internal room type ID
    room_type_name: str   # Human-readable room type (e.g. "Sea View Bungalow")
    dates: Set[str]       # Available dates as YYYY-MM-DD strings (mutable set for merging)


class RoomAvailabilityService:
    """Per-turn availability service.

    Holds a cache of PMS windows already fetched (`covered_ranges` +
    `rooms_availability`). This cache is only valid within a single graph
    invocation (one user turn) — PMS availability is live data, so instances
    must NOT be shared across turns or requests. Constructed per-invocation
    via `build_room_availability_svc()` in `services/scoped.py`.
    """

    def __init__(self, pms_client: PmsClient) -> None:
        self.pms_client = pms_client
        # List of [start, end) tuples covering what we have fetched from PMS
        self.covered_ranges: List[Tuple[datetime, datetime]] = []
        self.rooms_availability: Dict[str, InternalRoomAvailabilityData] = {}

    async def get_availability(
        self, search_start: datetime, search_end: datetime
    ) -> Dict[str, PmsRoomAvailability]:
        """
        Dynamically fetches missing chunks of availability to cover [search_start, search_end)
        and returns the strictly clipped availability for that exact window.
        """
        current_date = search_start
        while current_date < search_end:
            # Check if current_date is in any covered_range
            covered = False
            for c_start, c_end in self.covered_ranges:
                if c_start <= current_date < c_end:
                    covered = True
                    current_date = c_end
                    break

            if not covered:
                # Fetch a 14-day window from PMS starting from current_date
                pms_data = await self.pms_client.fetch_room_availability_window(
                    current_date.strftime("%Y-%m-%d")
                )
                pms_start = datetime.strptime(pms_data["from_date"], "%Y-%m-%d")
                pms_end = datetime.strptime(pms_data["to_date"], "%Y-%m-%d") + timedelta(
                    days=1
                )

                # Merge fetched dates into our state
                for room_no, room_info in pms_data["rooms"].items():
                    if room_no not in self.rooms_availability:
                        self.rooms_availability[room_no] = {
                            "room_id": room_info["room_id"],
                            "room_no": room_info["room_no"],
                            "room_type_id": room_info["room_type_id"],
                            "room_type_name": room_info["room_type_name"],
                            "dates": set(room_info["dates"]),
                        }
                    else:
                        self.rooms_availability[room_no]["dates"].update(
                            room_info["dates"]
                        )

                self.covered_ranges.append((pms_start, pms_end))
                # Sort ranges to ensure we jump optimally during coverage checks
                self.covered_ranges.sort(key=lambda x: x[0])
                current_date = pms_end

        # Now clip the merged data strictly to the requested [search_start, search_end)
        valid_dates = {
            (search_start + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((search_end - search_start).days)
        }
        result_rooms: Dict[str, PmsRoomAvailability] = {}
        for room_no, room_info in self.rooms_availability.items():
            filtered_dates = room_info["dates"].intersection(valid_dates)
            result_rooms[room_no] = {
                "room_id": room_info["room_id"],
                "room_no": room_info["room_no"],
                "room_type_id": room_info["room_type_id"],
                "room_type_name": room_info["room_type_name"],
                "dates": sorted(list(filtered_dates)),
            }

        return result_rooms
