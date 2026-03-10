import time
from dataclasses import dataclass, field, fields
from typing import List, Optional

from agent.utils.google_drive_client import read_spreadsheet_data

_ROOMS_INFO_PATH = "/cooper-project/data/rooms_info"
_CACHE_TTL = 600  # 10 minutes


@dataclass
class Room:
    room_name: str
    room_type: str
    summary: str
    beds: str
    baths: int
    size: float
    price_weekdays: float
    price_weekends_holidays: float
    price_ny_songkran: float
    max_guests: int
    steps_to_beach: int
    sea_view: int
    privacy: int
    steps_to_restaurant: int
    room_design: int
    room_newness: int
    tags: List[str] = field(default_factory=list)


_INT_FIELDS = {
    "bath",
    "max_guests",
    "steps_to_beach",
    "sea_view",
    "privacy",
    "steps_to_restaurant",
    "room_design",
    "room_newness",
}
_FLOAT_FIELDS = {
    "size",
    "price_weekdays",
    "price_weekends_holidays",
    "price_ny_songkran",
}


def _parse_room(raw: dict) -> Room:
    """Convert a raw spreadsheet row dict into a typed Room."""
    parsed = {}
    for f in fields(Room):
        value = raw.get(f.name, None)

        if f.name == "tags":
            parsed[f.name] = [t.strip() for t in (value or "").split(",") if t.strip()]
        elif f.name in _INT_FIELDS:
            parsed[f.name] = int(value) if value else 0
        elif f.name in _FLOAT_FIELDS:
            parsed[f.name] = float(value) if value else 0.0
        else:
            parsed[f.name] = str(value) if value else ""

    return Room(**parsed)


class RoomService:
    """Singleton service that fetches and caches rooms data of the hotel."""

    _instance: Optional["RoomService"] = None

    def __new__(cls) -> "RoomService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache: Optional[List[Room]] = None
            cls._instance._cache_expires_at: float = 0
        return cls._instance

    def get_all_rooms(self) -> List[Room]:
        """Return all rooms, cached for 10 minutes."""
        if self._cache is None or time.time() > self._cache_expires_at:
            raw_rows = read_spreadsheet_data(_ROOMS_INFO_PATH)
            self._cache = [_parse_room(row) for row in raw_rows]
            self._cache_expires_at = time.time() + _CACHE_TTL
        return self._cache

    def get_room_by_name(self, room_name: str) -> Optional[Room]:
        """Look up a single room by its room_name (e.g. 'S1', 'V2')."""
        room_name_lower = room_name.strip().lower()
        return next((r for r in self.get_all_rooms() if r.room_name.lower() == room_name_lower), None)

    def get_valid_room_names(self) -> List[str]:
        """Return a list of all valid room names."""
        return [r.room_name.lower() for r in self.get_all_rooms()]

    def does_room_exist(self, room_name: str) -> bool:
        """Check if a room name exists in the hotel."""
        return self.get_room_by_name(room_name) is not None

    def get_valid_rooms_list_str(self) -> str:
        """Get a comma-separated list of all valid rooms."""
        return ", ".join([r.room_name.upper() for r in self.get_all_rooms()])

    def validate_room(self, room_name: str) -> str | None:
        """
        Returns an error message string if the room is invalid, 
        or None if it is valid. This provides graceful tool errors.
        """
        if not self.does_room_exist(room_name):
            return f"Error: Room '{room_name}' does not exist. Please inform the user or choose from the valid rooms: {self.get_valid_rooms_list_str()}"
        return None


# Module-level singleton for convenient imports
room_service = RoomService()
