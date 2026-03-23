from datetime import datetime

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent.pricing import calculate_stay_pricing
from agent.schemas import ClosingState, PricingSummary, RoomCard, RoomSelection


def _find_room(rooms: list[RoomCard], room_name: str) -> RoomCard | None:
    """Find a room by room_name (case-insensitive)."""
    for r in rooms:
        if r.room_name.lower() == room_name.lower():
            return r
    return None


def _is_stay_available(room: RoomCard, check_in: str, check_out: str) -> bool:
    """Check if the requested stay fits within any available date range."""
    if not room.availability:
        return False
    for dr in room.availability.date_ranges:
        if check_in >= dr.start_date and check_out <= dr.end_date:
            return True
    return False


def _format_available_ranges(room: RoomCard) -> str:
    """Format available date ranges for error messages."""
    if not room.availability:
        return "none"
    return ", ".join(
        f"{dr.start_date} to {dr.end_date}" for dr in room.availability.date_ranges
    )


def _format_pricing_breakdown(pricing) -> str:
    """Format StayPricing breakdown into human-readable text."""
    lines = []
    for item in pricing.breakdown:
        lines.append(
            f"{item.tier}: {item.nights} night(s) x {item.rate:,.0f} = {item.subtotal:,.0f} THB"
        )
    if pricing.extra_bed:
        lines.append(
            f"Extra bed: {pricing.extra_bed.nights} night(s) x "
            f"{pricing.extra_bed.rate_per_night:,.0f} = {pricing.extra_bed.subtotal:,.0f} THB"
        )
    lines.append(f"Total: {pricing.total_price:,.0f} THB")
    return "\n".join(lines)


def _build_status_summary(
    selected_rooms: list[RoomSelection],
    search_rooms: list[RoomCard],
    total_guests: int,
) -> str:
    """Build a status summary of all selected rooms, pricing, and capacity."""
    lines = ["--- Selection Status ---"]

    for sel in selected_rooms:
        bed_label = " (+extra bed)" if sel.extra_bed else ""
        lines.append(
            f"- {sel.room_name}{bed_label}: {sel.check_in} to {sel.check_out} | "
            f"{sel.pricing.total_price:,.0f} THB"
        )

    grand_total = sum(r.pricing.total_price for r in selected_rooms)
    lines.append(f"Grand Total: {grand_total:,.0f} THB")

    # Capacity info
    total_capacity = 0
    for sel in selected_rooms:
        search_room = _find_room(search_rooms, sel.room_name)
        if search_room:
            total_capacity += search_room.max_guests
    max_with_beds = total_capacity + len(selected_rooms)
    lines.append(
        f"Capacity: {total_capacity} base + {len(selected_rooms)} extra beds max = "
        f"{max_with_beds} max | Guests: {total_guests}"
    )

    return "\n".join(lines)


def _error(msg: str, tool_call_id: str) -> Command:
    return Command(
        update={"messages": [ToolMessage(content=msg, tool_call_id=tool_call_id)]}
    )


@tool
async def select_room(
    room_name: str,
    check_in: str,
    check_out: str,
    extra_bed: bool = False,
    runtime: ToolRuntime = None,
) -> Command:
    """Select a room and lock in check-in/check-out dates. Call once per room.
    If the same room is already selected, it will be replaced with the new dates/settings.

    Args:
        room_name: Room name from the search results (e.g. "s5", "v2").
        check_in: Check-in date in YYYY-MM-DD format.
        check_out: Check-out date in YYYY-MM-DD format.
        extra_bed: Set to true to add an extra bed to this room (500 THB/night). Only set when user explicitly requests it or when instructed by a previous tool response.
    """
    search_result = runtime.state.get("room_search_result")
    if not search_result or not search_result.rooms:
        return _error("No search results available for room selection.", runtime.tool_call_id)

    criteria = runtime.state.get("criteria")

    # Guard: total_guests required
    if not criteria or not criteria.total_guests:
        return _error(
            "Cannot select a room without knowing the total number of guests. "
            "Please ask the user how many guests will be staying.",
            runtime.tool_call_id,
        )

    total_guests = criteria.total_guests

    # Find room in search results
    room = _find_room(search_result.rooms, room_name)
    if not room:
        valid = ", ".join(r.room_name for r in search_result.rooms)
        return _error(
            f"Room '{room_name}' not found in search results. Available rooms: {valid}",
            runtime.tool_call_id,
        )

    # Validate dates
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return _error("Invalid date format. Use YYYY-MM-DD.", runtime.tool_call_id)

    if check_out_dt <= check_in_dt:
        return _error("check_out must be after check_in.", runtime.tool_call_id)

    # Validate availability
    if not _is_stay_available(room, check_in, check_out):
        ranges = _format_available_ranges(room)
        return _error(
            f"Room {room_name} is not available for {check_in} to {check_out}. "
            f"Available date ranges: {ranges}",
            runtime.tool_call_id,
        )

    # Calculate pricing
    nightly_rates = room.availability.nightly_rates
    stay_pricing = calculate_stay_pricing(
        check_in, check_out, nightly_rates, extra_bed_required=extra_bed
    )
    breakdown_text = _format_pricing_breakdown(stay_pricing)
    extra_bed_note = (
        f"Extra bed: {stay_pricing.extra_bed.nights} night(s) x "
        f"{stay_pricing.extra_bed.rate_per_night:,.0f} THB = {stay_pricing.extra_bed.subtotal:,.0f} THB"
        if stay_pricing.extra_bed
        else None
    )

    new_selection = RoomSelection(
        room_name=room.room_name,
        check_in=check_in,
        check_out=check_out,
        extra_bed=extra_bed,
        pricing=PricingSummary(
            total_price=stay_pricing.total_price,
            breakdown_text=breakdown_text,
            extra_bed_note=extra_bed_note,
        ),
    )

    # Build updated selected_rooms list (replace if same room, else append)
    closing_state: ClosingState = runtime.state.get("closing_state") or ClosingState()
    updated_rooms = [
        r for r in closing_state.selected_rooms
        if r.room_name.lower() != room_name.lower()
    ]
    updated_rooms.append(new_selection)

    # Capacity check across ALL selected rooms
    total_capacity = 0
    for sel in updated_rooms:
        sr = _find_room(search_result.rooms, sel.room_name)
        if sr:
            total_capacity += sr.max_guests
    max_with_extra_beds = total_capacity + len(updated_rooms)

    if total_guests > max_with_extra_beds:
        # HARD BLOCK — can't fit even with extra beds in every room
        return _error(
            f"Cannot accommodate {total_guests} guests. "
            f"Current selection ({len(updated_rooms)} room(s)) has base capacity {total_capacity} "
            f"+ max {len(updated_rooms)} extra bed(s) = {max_with_extra_beds} max. "
            f"Resort policy: max 1 extra bed per room. "
            f"Please select additional rooms or adjust guest count.",
            runtime.tool_call_id,
        )

    # Extra bed detection
    notes = []
    nights = (check_out_dt - check_in_dt).days
    notes.append(
        f"Room {room.room_name} ({room.room_type}) selected. "
        f"{check_in} to {check_out} ({nights} night(s))."
    )
    notes.append(f"Pricing:\n{breakdown_text}")

    if total_guests > total_capacity:
        extra_beds_needed = total_guests - total_capacity
        existing_extra_beds = sum(1 for r in updated_rooms if r.extra_bed)

        if len(updated_rooms) == 1 and not extra_bed:
            # Auto-assign extra bed for single room
            stay_pricing = calculate_stay_pricing(
                check_in, check_out, nightly_rates, extra_bed_required=True
            )
            breakdown_text = _format_pricing_breakdown(stay_pricing)
            extra_bed_note = (
                f"Extra bed: {stay_pricing.extra_bed.nights} night(s) x "
                f"{stay_pricing.extra_bed.rate_per_night:,.0f} THB = {stay_pricing.extra_bed.subtotal:,.0f} THB"
                if stay_pricing.extra_bed
                else None
            )
            new_selection = RoomSelection(
                room_name=room.room_name,
                check_in=check_in,
                check_out=check_out,
                extra_bed=True,
                pricing=PricingSummary(
                    total_price=stay_pricing.total_price,
                    breakdown_text=breakdown_text,
                    extra_bed_note=extra_bed_note,
                ),
            )
            updated_rooms = [new_selection]
            notes.append(
                f"Extra bed auto-assigned ({total_guests} guests, room fits {room.max_guests}). "
                f"Updated pricing:\n{breakdown_text}"
            )
        elif extra_beds_needed > existing_extra_beds:
            remaining = extra_beds_needed - existing_extra_beds
            rooms_without_bed = [
                r.room_name for r in updated_rooms if not r.extra_bed
            ]
            notes.append(
                f"WARNING: {total_guests} guests exceed base capacity ({total_capacity}). "
                f"{remaining} more extra bed(s) needed. "
                f"Ask user which room(s) should have the extra bed: {', '.join(rooms_without_bed)}. "
                f"Then call select_room again with extra_bed=true for the chosen room(s)."
            )

    # Build updated closing state
    updated_state = ClosingState(
        selected_rooms=updated_rooms,
        terms_and_payment_shown=False,  # Reset — selection changed
    )

    # Append status summary
    status = _build_status_summary(updated_rooms, search_result.rooms, total_guests)
    notes.append(status)

    return Command(
        update={
            "closing_state": updated_state,
            "messages": [
                ToolMessage(
                    content="\n\n".join(notes),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
