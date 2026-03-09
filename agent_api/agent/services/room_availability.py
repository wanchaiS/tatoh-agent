from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Tuple, TypedDict

from agent.utils.pms_client import fetch_room_availability_window


class RoomAvailabilityData(TypedDict):
    room_id: str
    room_no: str
    room_type_id: str
    room_type_name: str
    dates: List[str]


class InternalRoomAvailabilityData(TypedDict):
    room_id: str
    room_no: str
    room_type_id: str
    room_type_name: str
    dates: Set[str]


class RoomAvailabilityService:
    def __init__(self):
        # List of [start, end) tuples covering what we have fetched from PMS
        self.covered_ranges: List[Tuple[datetime, datetime]] = []
        self.rooms_availability: Dict[str, InternalRoomAvailabilityData] = {}

    def get_availability(
        self, search_start: datetime, search_end: datetime
    ) -> Dict[str, RoomAvailabilityData]:
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
                pms_data = fetch_room_availability_window(
                    current_date.strftime("%Y-%m-%d")
                )
                pms_start = datetime.strptime(pms_data["from"], "%Y-%m-%d")
                pms_end = datetime.strptime(pms_data["to"], "%Y-%m-%d") + timedelta(
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
        result_rooms = {}
        for room_no, room_info in self.rooms_availability.items():
            filtered_dates = room_info["dates"].intersection(valid_dates)
            result_rooms[room_no] = {**room_info, "dates": sorted(list(filtered_dates))}

        return result_rooms
