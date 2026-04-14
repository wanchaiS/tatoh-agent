from typing import TypedDict
from core.photo_helpers import EmbeddedPhoto


class InternalRoom(TypedDict):
    id: int
    room_name: str
    room_type: str
    summary: str
    bed_queen: int
    bed_single: int
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
    tags: list[str]
    thumbnail_url: str
    photos: list[EmbeddedPhoto]


class RoomCard(TypedDict):
    id: int
    room_name: str
    room_type: str
    summary: str
    bed_queen: int
    bed_single: int
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
    tags: list[str]
    thumbnail_url: str
    photos: list[EmbeddedPhoto]
    date_ranges: list[dict[str, str]]


MAP_SRC = "/static/photos/maps/resort_map.jpeg"

ROOM_PIN_POSITIONS: dict[int, dict[str, float]] = {
    18: {"x": 88.4, "y": 47.6},   # S1
    19: {"x": 66.5, "y": 47.4},   # S2
    20: {"x":  8.8, "y": 50.2},   # S3
    21: {"x": 25.6, "y": 69.7},   # S4
    22: {"x": 40.6, "y": 47.0},   # S5
    23: {"x": 44.0, "y": 85.6},   # S6
    24: {"x":  8.2, "y": 87.0},   # S7
    25: {"x": 70.7, "y": 68.3},   # S8
    26: {"x": 56.3, "y": 86.4},   # S9
    27: {"x":  9.7, "y": 36.7},   # S10
    28: {"x": 29.8, "y": 34.5},   # S11
    29: {"x": 61.5, "y": 38.0},   # S12
    30: {"x": 82.1, "y": 38.4},   # S14
    31: {"x": 26.1, "y": 87.2},   # V1
    32: {"x": 50.9, "y": 69.9},   # V2
    33: {"x": 92.9, "y": 58.8},   # V3
}
