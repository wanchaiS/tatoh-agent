from typing import Optional

from pydantic import BaseModel


class RoomCreate(BaseModel):
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
    tags: Optional[str] = None


class RoomUpdate(BaseModel):
    room_name: Optional[str] = None
    room_type: Optional[str] = None
    summary: Optional[str] = None
    bed_queen: Optional[int] = None
    bed_single: Optional[int] = None
    baths: Optional[int] = None
    size: Optional[float] = None
    price_weekdays: Optional[float] = None
    price_weekends_holidays: Optional[float] = None
    price_ny_songkran: Optional[float] = None
    max_guests: Optional[int] = None
    steps_to_beach: Optional[int] = None
    sea_view: Optional[int] = None
    privacy: Optional[int] = None
    steps_to_restaurant: Optional[int] = None
    room_design: Optional[int] = None
    room_newness: Optional[int] = None
    tags: Optional[str] = None


class RoomResponse(BaseModel):
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
    tags: Optional[str] = None

    model_config = {"from_attributes": True}
