import json
from datetime import datetime

from agent.closing_phase.schemas import ClosingState
from agent.common_tools.record_visiting_info import VisitingInfo
from agent.common_tools.record_preference import UserPreferences
from agent.common_tools import (
    deselect_room,
    find_boat_schedules,
    get_booking_terms_and_payment,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_info,
    get_rooms_list,
    record_visiting_info,
    record_preference,
    revise_criteria,
    search_available_rooms,
    select_room,
    update_guest_count,
)
from agent.services.room_schemas import RoomCard
from agent.types import GlobalState
from agent.search_phase.prompts import get_criteria_discovery_prompt

# ── Shared Q&A tools (available in all phases) ──────────────────────────
shared_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_info,
    get_rooms_list,
    record_visiting_info,
    record_preference,
]

# ── Tool sets per phase ─────────────────────────────────────────────────
PHASE_TOOLS = {
    "criteria_discovery": shared_tools + [search_available_rooms],
    "closing": shared_tools + [
        revise_criteria, select_room, deselect_room,
        update_guest_count, get_booking_terms_and_payment,
    ],
}


def get_prompt_and_tools(state: GlobalState) -> tuple[str, list]:
    """Return (system_prompt, tools) based on current phase. Called every agent loop iteration."""
    phase = state.get("phase", "criteria_discovery")
    today = datetime.now().strftime("%Y-%m-%d")
    user_preferences = _build_preferences_context(state.get("preferences") or UserPreferences())
    booking_info = _build_booking_info_context(state.get("booking_info") or VisitingInfo())
    
    if phase == "criteria_discovery":
        prompt = get_criteria_discovery_prompt(today, user_preferences, booking_info)
    elif phase == "closing":
        prompt = _build_closing_prompt(
            state.get("closing_state") or ClosingState(),
            state.get("aggregated_room_search_results"),
            today,
            preferences,
            booking_info,
        )
    else:
        raise ValueError(f"No prompt defined for phase: {phase}")

    tools = PHASE_TOOLS.get(phase, shared_tools)
    return prompt, tools


# ── Preferences Context Helper ──────────────────────────────────────────

def _build_preferences_context(preferences: UserPreferences) -> str:
    """Format known user preferences as a plain-English block for prompt injection."""
    data = preferences.model_dump(exclude_none=True)
    if not data:
        return "None captured yet."

    lines = []
    loc = data.get("location_preference")
    if loc:
        label = {
            "beach_side": "beach-side (closer to beach, longer walk to facilities)",
            "middle": "middle of the hill (balanced — decent view, manageable walk both ways)",
            "facilities_side": "facilities-side (closer to restaurant/reception, farther from beach)",
        }.get(loc, loc)
        lines.append(f"- Location preference: {label}")
    if data.get("privacy_preferred"):
        lines.append("- Wants privacy / seclusion")
    group = data.get("group_type")
    if group:
        lines.append(f"- Group type: {group}")
    if data.get("mobility_limited"):
        lines.append("- Mobility consideration: one or more guests may have difficulty with slopes or long walks")
    return "\n".join(lines)


# ── Booking Info Context Helper ────────────────────────────────────────

def _build_booking_info_context(booking_info: VisitingInfo) -> str:
    """Format known booking info as a plain-English block for prompt injection."""
    data = booking_info.model_dump(exclude_none=True)
    if not data:
        return "None captured yet."

    lines = []
    if "guest_count" in data:
        lines.append(f"- Guest count: {data['guest_count']}")
    if "duration_nights" in data:
        lines.append(f"- Duration: {data['duration_nights']} nights")
    if "check_in_date" in data:
        lines.append(f"- Check-in: {data['check_in_date']}")
    if "check_out_date" in data:
        lines.append(f"- Check-out: {data['check_out_date']}")
    return "\n".join(lines)


# ── Criteria Discovery Prompt ───────────────────────────────────────────


# ── Closing Prompt ──────────────────────────────────────────────────────

def _build_rooms_context(room_cards: list[RoomCard]) -> str:
    """Build a summary of available rooms for injection into the system prompt."""
    if not room_cards:
        return "No search results."
    lines = [f"Found {len(room_cards)} rooms:"]
    for r in room_cards:
        if r.availability:
            dates_str = ", ".join(
                f"{dr.start_date} to {dr.end_date}" for dr in r.availability.date_ranges
            )
            rates = r.availability.nightly_rates
            rates_str = (
                f"rates: weekday {rates.weekday:,.0f} / "
                f"weekend {rates.weekend:,.0f} / "
                f"holiday {rates.holiday:,.0f}"
            )
        else:
            dates_str = "N/A"
            rates_str = ""
        lines.append(
            f"  - {r.room_name} ({r.room_type}) | max {r.max_guests} guests | "
            f"available: {dates_str} | {rates_str}"
        )
    return "\n".join(lines)


def _build_closing_context(closing_state: ClosingState) -> str:
    """Build closing state context for prompt injection."""
    parts = []
    if closing_state.selected_rooms:
        parts.append(f"Selected Rooms ({len(closing_state.selected_rooms)}):")
        for r in closing_state.selected_rooms:
            bed_label = " (+extra bed)" if r.extra_bed else ""
            parts.append(
                f"  - {r.room_name}{bed_label}: {r.check_in} to {r.check_out} | "
                f"{r.pricing.total_price:,.0f} THB"
            )
        parts.append(f"Grand Total: {closing_state.total_price:,.0f} THB")
    if closing_state.terms_and_payment_shown:
        parts.append("Terms & payment info: Already presented to user.")
    return "\n".join(parts) if parts else "No rooms selected yet."


def _get_step_instructions(step: str, closing_state: ClosingState) -> str:
    """Return step-specific behavioral instructions for the closing prompt."""
    if step == "browsing":
        return """The search results are in conversation history. Room cards are displayed in the UI.
Your goals:
1. Help the user choose room(s) — answer questions, compare rooms using the data in [AVAILABLE ROOMS FROM SEARCH].
2. Users may need MULTIPLE rooms (e.g. groups, families). Call `select_room` once per room.
3. When the user indicates interest in a room, ensure you have both room_name AND specific dates.
   - If they only say a room number (e.g. "เอา S5"), check the room's available date ranges.
   - If the room has ONE available range and criteria has duration_nights → suggest dates and ASK to confirm.
   - If the room has MULTIPLE available ranges → ask which range they prefer.
4. ALWAYS confirm room + dates with the user BEFORE calling `select_room`.
5. Guest count is REQUIRED before calling `select_room` (needed for capacity check and pricing). If not set yet, ask naturally: "กี่ท่านคะ?"
6. If the user wants to change search criteria (dates, duration), call `revise_criteria`.
7. To remove a previously selected room, call `deselect_room`."""

    elif step == "pending_terms_payment":
        rooms_summary = "\n".join(
            f"  - {r.room_name}{' (+extra bed)' if r.extra_bed else ''}: "
            f"{r.check_in} to {r.check_out} | {r.pricing.total_price:,.0f} THB"
            for r in closing_state.selected_rooms
        )
        return f"""The user has selected room(s):
{rooms_summary}
Grand Total: {closing_state.total_price:,.0f} THB

ACTION REQUIRED: Call `get_booking_terms_and_payment` NOW to retrieve booking terms and bank payment info, then present them to the user warmly.
If the user wants to add/change/remove rooms, use `select_room` or `deselect_room`.
If the user wants to change search criteria, call `revise_criteria`."""

    elif step == "awaiting_proof":
        rooms_list = ", ".join(r.room_name for r in closing_state.selected_rooms)
        return f"""Booking terms and payment info have been presented.
Selected rooms: {rooms_list}
Grand Total: {closing_state.total_price:,.0f} THB

The user should transfer payment and send proof (photo/screenshot).
- Gently remind them if needed, but don't be pushy.
- Answer any remaining questions about the resort or their stay.
- If they want to change rooms, use `select_room` / `deselect_room`.
- If they want to change search criteria, call `revise_criteria`."""

    return ""


