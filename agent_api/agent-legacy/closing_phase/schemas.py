from typing import List

from agent.pricing import StayPricing
from pydantic import BaseModel, Field


class RoomSelection(BaseModel):
    """A single room selection with its pricing."""
    room_name: str
    check_in: str
    check_out: str
    extra_bed: bool = False
    pricing: StayPricing


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
