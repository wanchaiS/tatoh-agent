from datetime import datetime, timedelta
from typing import List, Optional

from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ── User Preferences ───────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    """
    Soft preferences passively collected from the conversation.
    All fields are optional — only set when clearly inferred from what the user said.
    Used as context for the agent when answering questions or making recommendations.
    """

    location_preference: Optional[str] = Field(
        None,
        description=(
            "The user's preferred position on the resort hill. "
            "The resort is built on a slope: rooms closer to the beach are lower on the hill (better sea view, "
            "more walking to reach the main road/reception/restaurant), while rooms near the top are closer to "
            "facilities but farther from the beach. "
            "Set to 'beach_side' if they prioritise beach access or sea view. "
            "Set to 'facilities_side' if they prefer easy access to the restaurant, reception, or main road. "
            "Set to 'middle' if they want a balance of both. "
            "Valid values: 'beach_side', 'middle', 'facilities_side'."
        ),
    )
    privacy_preferred: Optional[bool] = Field(
        None,
        description=(
            "Set to True if the user expresses a desire for seclusion, "
            "a quiet/private spot, or wants to be away from other guests. "
            "E.g. 'we'd like somewhere secluded', 'honeymoon, want privacy'."
        ),
    )
    group_type: Optional[str] = Field(
        None,
        description=(
            "The type of group travelling. Use to tailor recommendations. "
            "Set to 'couple' for two adults (especially if honeymoon/romantic trip). "
            "Set to 'family' if they mention children or parents travelling together. "
            "Set to 'friends' for a group of adults without a romantic/family context. "
            "Set to 'solo' for a single traveller. "
            "Valid values: 'couple', 'family', 'friends', 'solo'."
        ),
    )
    mobility_limited: Optional[bool] = Field(
        None,
        description=(
            "Set to True if any guest in the party may have difficulty with slopes or long walks. "
            "This includes: elderly guests, guests with a physical condition (bad knee, back problems), "
            "guests travelling with a baby stroller, or anyone who explicitly mentions difficulty walking. "
            "This strongly influences location recommendations — mobility-limited guests should avoid "
            "rooms that are far down the hill (long uphill walk back to facilities)."
        ),
    )


# ── Criteria (was criteria_discovery/schema.py) ─────────────────────────


class DateWindow(BaseModel):
    start_date: str = Field(..., description="Start of the search window (YYYY-MM-DD).")
    end_date: str = Field(..., description="End of the search window (YYYY-MM-DD).")

    def window_days(self) -> int:
        """Total span of this window in days."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        return (end - start).days


class Criteria(BaseModel):
    """Search criteria for booking."""

    date_windows: List[DateWindow] = Field(default_factory=list)
    duration_nights: Optional[int] = Field(None)
    total_guests: Optional[int] = Field(None)
    requested_rooms: Optional[List[str]] = Field(None)
    requested_room_types: Optional[List[str]] = Field(None)

    def get_expanded_windows(self, expanded_days: int) -> List[tuple[str, str]]:
        """
        Return each window expanded by ±expanded_days.
        Used as fallback when all windows return no rooms.
        """
        result = []
        for w in self.date_windows:
            try:
                start_dt = datetime.strptime(w.start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(w.end_date, "%Y-%m-%d")
            except ValueError:
                result.append((w.start_date, w.end_date))
                continue
            if expanded_days and expanded_days > 0:
                result.append(
                    (
                        (start_dt - timedelta(days=expanded_days)).strftime("%Y-%m-%d"),
                        (end_dt + timedelta(days=expanded_days)).strftime("%Y-%m-%d"),
                    )
                )
            else:
                result.append((w.start_date, w.end_date))
        return result

    def get_criteria_id(self) -> str:
        windows_key = "_".join(
            f"{w.start_date}-{w.end_date}"
            for w in sorted(self.date_windows, key=lambda w: w.start_date)
        )
        return f"{windows_key}_{self.duration_nights}"


class PendingUIItem(TypedDict):
    name: str
    props: dict
    id: str


# ── Closing (was closing/schema.py) ─────────────────────────────────────


class PricingSummary(BaseModel):
    total_price: float
    breakdown_text: str
    extra_bed_note: Optional[str] = None


class RoomSelection(BaseModel):
    """A single room selection with its pricing."""
    room_name: str
    check_in: str
    check_out: str
    extra_bed: bool = False
    pricing: PricingSummary


class ClosingState(BaseModel):
    selected_rooms: List[RoomSelection] = Field(default_factory=list)
    terms_and_payment_shown: bool = False

    @property
    def current_step(self) -> str:
        if not self.selected_rooms:
            return "browsing"
        if not self.terms_and_payment_shown:
            return "pending_terms_payment"
        return "awaiting_proof"

    @property
    def total_price(self) -> float:
        return sum(r.pricing.total_price for r in self.selected_rooms)


# ── Room Card DTO ─────────────────────────────────────────────────────


class Rates(BaseModel):
    weekday: float
    weekend: float
    holiday: float


class DateRange(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")


class RoomAvailability(BaseModel):
    """Search-specific availability info, only present on RoomCards from search results."""
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
    def from_db(cls, db_room, thumbnail_url: str | None = None) -> "RoomCard":
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


class PriceBreakdownItem(BaseModel):
    tier: str
    nights: int
    rate: float
    subtotal: float


class ExtraBedInfo(BaseModel):
    nights: int
    rate_per_night: float = 500.0
    subtotal: float = 0.0

    def model_post_init(self, __context):
        if self.subtotal == 0:
            object.__setattr__(self, "subtotal", self.nights * self.rate_per_night)


class StayPricing(BaseModel):
    total_price: float
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None
