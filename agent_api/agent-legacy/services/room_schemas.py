from typing import List

from pydantic import BaseModel, Field


class Rates(BaseModel):
    weekday: float
    weekend: float
    holiday: float


class DateRange(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")


class RoomAvailability(BaseModel):
    """Search-specific availability info, only present on RoomCards from search results."""
    dates: List[str] = Field(default_factory=list)  # raw available dates from PMS
    date_ranges: List[DateRange]
    nightly_rates: Rates
    extra_bed_required: bool = False


class RoomCard(BaseModel):
    """Unified DTO for a room — used in search results, get_room_info, get_rooms_list."""
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
    tags: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    availability: RoomAvailability | None = None

    @classmethod
    def from_db(cls, db_room, thumbnail_url: str | None = None) -> RoomCard:
        """Convert a SQLAlchemy Room model to a RoomCard."""
        raw_tags = getattr(db_room, "tags", None)
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = raw_tags
        else:
            tags = []

        return cls(
            id=db_room.id,
            room_name=db_room.room_name,
            room_type=db_room.room_type,
            summary=db_room.summary,
            bed_queen=db_room.bed_queen,
            bed_single=db_room.bed_single,
            baths=db_room.baths,
            size=db_room.size,
            price_weekdays=db_room.price_weekdays,
            price_weekends_holidays=db_room.price_weekends_holidays,
            price_ny_songkran=db_room.price_ny_songkran,
            max_guests=db_room.max_guests,
            steps_to_beach=db_room.steps_to_beach,
            sea_view=db_room.sea_view,
            privacy=db_room.privacy,
            steps_to_restaurant=db_room.steps_to_restaurant,
            room_design=db_room.room_design,
            room_newness=db_room.room_newness,
            tags=tags,
            thumbnail_url=thumbnail_url,
        )


class RoomSearchResult(BaseModel):
    rooms: List[RoomCard]
    criteria_id: str
    expanded_days: int
    exhausted: bool
    search_results_summary: str
