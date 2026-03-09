from typing import Literal, Optional

from pydantic import BaseModel

ClosingStep = Literal[
    "consulting",
    "room_selected",
    "tos_accepted",
    "payment_presented",
    "awaiting_staff",
    "booking_confirmed",
]


class SelectedStay(BaseModel):
    room_no: str
    check_in: str
    check_out: str


class PricingSummary(BaseModel):
    total_price: float
    breakdown_text: str
    extra_bed_note: Optional[str] = None


class ClosingState(BaseModel):
    closing_step: ClosingStep = "consulting"
    selected_stay: Optional[SelectedStay] = None
    pricing: Optional[PricingSummary] = None
    tos_accepted: bool = False
    payment_presented: bool = False
    staff_confirmed: bool = False
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
