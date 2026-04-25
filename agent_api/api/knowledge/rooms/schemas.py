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
    tags: str | None = None


class RoomUpdate(BaseModel):
    room_name: str | None = None
    room_type: str | None = None
    summary: str | None = None
    bed_queen: int | None = None
    bed_single: int | None = None
    baths: int | None = None
    size: float | None = None
    price_weekdays: float | None = None
    price_weekends_holidays: float | None = None
    price_ny_songkran: float | None = None
    max_guests: int | None = None
    steps_to_beach: int | None = None
    sea_view: int | None = None
    privacy: int | None = None
    steps_to_restaurant: int | None = None
    room_design: int | None = None
    room_newness: int | None = None
    tags: str | None = None


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
    tags: str | None = None

    model_config = {"from_attributes": True}
