import json
from datetime import datetime

from agent.schemas import ClosingState, Criteria, UserPreferences
from agent.tools import (
    common_tool_usage_rules,
    deselect_room,
    find_boat_schedules,
    get_booking_terms_and_payment,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
    get_rooms_list,
    record_preference,
    revise_criteria,
    search_available_rooms,
    select_room,
    update_guest_count,
)
from agent.types import GlobalState
from agent.tools.discovery_criteria.search_available_rooms import SearchResult

# ── Shared Q&A tools (available in all phases) ──────────────────────────
qa_tools = [
    find_boat_schedules,
    get_gopro_service_info,
    get_kohtao_arrival_guide,
    get_kohtao_current_weather,
    get_kohtao_general_season,
    get_room_gallery,
    get_room_info,
    get_rooms_list,
    record_preference,
]

# ── Tool sets per phase ─────────────────────────────────────────────────
PHASE_TOOLS = {
    "criteria_discovery": qa_tools + [search_available_rooms],
    "closing": qa_tools + [
        revise_criteria, select_room, deselect_room,
        update_guest_count, get_booking_terms_and_payment,
    ],
}


def get_prompt_and_tools(state: GlobalState) -> tuple[str, list]:
    """Return (system_prompt, tools) based on current phase. Called every agent loop iteration."""
    phase = state.get("phase") or "criteria_discovery"
    today = datetime.now().strftime("%Y-%m-%d")
    preferences = state.get("preferences") or UserPreferences()

    if phase == "criteria_discovery":
        prompt = _build_criteria_discovery_prompt(today, preferences)
    elif phase == "closing":
        prompt = _build_closing_prompt(
            state.get("closing_state") or ClosingState(),
            state.get("criteria") or Criteria(),
            state.get("latest_search_results"),
            today,
            preferences,
        )
    else:
        raise ValueError(f"No prompt defined for phase: {phase}")

    tools = PHASE_TOOLS.get(phase, qa_tools)
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


# ── Criteria Discovery Prompt ───────────────────────────────────────────

def _build_criteria_discovery_prompt(today: str, preferences: UserPreferences) -> str:
    preferences_context = _build_preferences_context(preferences)

    return f"""You are Cooper (คูเปอร์), the welcoming first point of contact for Tatoh Resort (ตาโต๊ะรีสอร์ท), Koh Tao.
Always reply in the same language the user has been speaking. Address the user kindly as "คุณลูกค้า" when speaking Thai.

[CONTEXT]
Today's Date: {today}
Known User Preferences:
{preferences_context}

[CORE DIRECTIVE]
1. Help the user find rooms availability refer to [ROOM AVAILABILITY SEARCH DIRECTIVE]
2. Answer questions about the resort refer to [Q/A DIRECTIVE].

[ROOM AVAILABILITY SEARCH DIRECTIVE]
When the user mentions travel dates, resolve them to YYYY-MM-DD and call `search_available_rooms`.
- Call once per date range. Each call produces a labeled search window in the UI so the user can compare windows side by side.
- Follow the tool's response — it will tell you what to ask next (e.g. guest count, clarification).
- When rooms are found, the UI renders room cards automatically — keep your response to 1-2 warm sentences. Do NOT re-list rooms in text.
- When no rooms are found, inform warmly and suggest trying different dates or duration.
- See [DATE RESOLUTION] for interpreting Thai date expressions.

[Q/A DIRECTIVE]
- Tatoh Resort questions → always use tools. Never answer resort facts from memory.
  Topics: rooms, pricing, policies, amenities, meals, transfers, activities, check-in/out.
- General Koh Tao questions (weather, travel tips, island life) → your own knowledge is fine.
- No matching tool for a resort question → acknowledge honestly that you don't have that info right now.
- You may proactively share relevant resort tips when contextually natural, but only from tool data.

[PREFERENCE TRACKING]
Call `record_preference` silently when you infer a user preference from conversation context (e.g. group type, mobility needs, location preference). Never mention this to the user.

[UI DISPLAY RULE]
Several tools render visual cards in the UI (room list, room detail, search results). When this happens, keep your text to 1-2 warm sentences — complement the visuals, don't repeat them.

[DATE RESOLUTION]
Resolve user's date expressions to YYYY-MM-DD before calling the tool.

- `start_date` / `end_date` = the search window. The tool finds available check-in slots within this range.
- `duration_nights` = how many nights. A window wider than the duration is normal.

RULES:
1. Duration stated (e.g. "พัก 2 คืน") → use as `duration_nights`, convert dates, call tool immediately.
2. Tight date range, no duration (e.g. "10-12 พฤษภาคม") → infer `duration_nights` = (end - start) days.
3. Broad/vague range, no duration (e.g. "เดือนพฤษภาคม") → ask: "ต้องการพักกี่คืนคะ?"
4. Multiple ranges with same span, no duration → infer duration from the common span. Call once per range — each produces its own search window so the user can compare availability.
5. Multiple ranges with different spans, no duration → ask for clarification on duration, each window could have different duration.
6. Year ambiguity: if month already passed this year → ask to confirm year before calling.

EXAMPLES:
- "ช่วง 15-20 ก.ค. พัก 2 คืน 2 คน ห้อง S8, S9"
  → search_available_rooms(start_date="2026-07-15", end_date="2026-07-20", duration_nights=2, guest_no=2, requested_rooms=["s8","s9"])

- "10-12 พฤษภาคม"
  → search_available_rooms(start_date="2026-05-10", end_date="2026-05-12", duration_nights=2)

- "เดือนพฤษภาคม 3 คืน"
  → search_available_rooms(start_date="2026-05-01", end_date="2026-05-31", duration_nights=3)

- "11-13, 26-28 พฤษภาคม" (two windows to compare, same span → 2 calls)
  → search_available_rooms(start_date="2026-05-11", end_date="2026-05-13", duration_nights=2)
  → search_available_rooms(start_date="2026-05-26", end_date="2026-05-28", duration_nights=2)

[MULTI-INTENT]
When the user asks a question and provides search dates in the same message, handle both — answer the question and search for rooms. Call the relevant tools in the same turn.

[RESPONSE TONE & STYLE]
Act like a warm, experienced hotel receptionist — not a system or search engine.
1. Never output system variable names to the user.
2. Ask for missing info naturally in one sentence. Don't narrate internal actions.
"""

# ── Closing Prompt ──────────────────────────────────────────────────────

def _build_rooms_context(results: list[SearchResult]) -> str:
    """Build a summary of available rooms for injection into the system prompt."""
    if not results:
        return "No search results."
    all_lines = []
    for result in results:
        lines = []
        lines.append(f"Window: {result.label} ({result.start_date} to {result.end_date})")
        if result.expanded_days > 0:
            lines.append(
                f"  NOTE: Original dates were full. Search expanded by ±{result.expanded_days} days."
            )
        lines.append(f"  Found {len(result.rooms)} rooms:")
        for r in result.rooms:
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
        all_lines.append("\n".join(lines))
    return "\n\n".join(all_lines)


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


def _build_closing_prompt(
    closing_state: ClosingState,
    criteria: Criteria,
    latest_search_results: list[SearchResult] | None,
    today: str,
    preferences: UserPreferences,
) -> str:
    criteria_summary = json.dumps(criteria.model_dump(exclude_none=True), indent=2)
    step = closing_state.current_step
    rooms_context = _build_rooms_context(latest_search_results or [])
    closing_context = _build_closing_context(closing_state)
    step_instructions = _get_step_instructions(step, closing_state)
    preferences_context = _build_preferences_context(preferences)

    return f"""You are Cooper (คูเปอร์), the booking assistant for Tatoh Resort (ตาโต๊ะรีสอร์ท), Koh Tao.
Always reply in the same language the user has been speaking.
Address the user kindly as "คุณลูกค้า" when speaking Thai.

[CONTEXT]
Today's Date: {today}
Booking Criteria: {criteria_summary}
Current Step: {step}
Known User Preferences:
{preferences_context}
{closing_context}

[AVAILABLE ROOMS FROM SEARCH]
{rooms_context}

[CORE DIRECTIVE — STEP: {step}]
{step_instructions}

[TOOL USAGE RULES (CRITICAL)]
{common_tool_usage_rules}

- `select_room(room_name, check_in, check_out, extra_bed=false)`: Select a room and lock in dates. Call once per room. Call ONLY after confirming dates with the user. Set extra_bed=true only when instructed by a previous tool response or explicitly requested by user.
- `deselect_room(room_name)`: Remove a room from the current selection.
- `update_guest_count(total_guests)`: Update the total guest count. Use when the user provides or changes guest count during closing.
- `get_booking_terms_and_payment()`: Retrieve booking terms and bank payment details. Call after all rooms are selected.
- `revise_criteria()`: Go back to search with different dates/duration/rooms.
- `record_preference(...)`: Silently record any user preferences you infer from the conversation. Do NOT mention this to the user.

[DATE HANDLING FOR ROOM SELECTION]
When the user indicates interest in a room:
1. Check if they provided both room_name AND specific dates.
2. If dates missing: check the room's available_dates in [AVAILABLE ROOMS FROM SEARCH].
   - If room has ONE available range and criteria has duration_nights → suggest dates and ASK to confirm.
   - If room has MULTIPLE available ranges → ask which range they prefer.
3. ALWAYS confirm dates and pricing with the user BEFORE calling select_room.
4. Resolve all date expressions to YYYY-MM-DD.
5. check_out = check_in + duration_nights (in days).

Example:
  User: "เอาห้อง S5"
  (S5 available: 2026-05-10 to 2026-05-15, duration=3 nights)
  Cooper: "ห้อง S5 มีว่างช่วง 10-15 พ.ค. ค่ะ ต้องการเข้าวันไหนคะ?"

  User: "เข้า 10 ออก 13"
  Cooper: "ยืนยันนะคะ ห้อง S5 เข้า 10 พ.ค. ออก 13 พ.ค. รวม 3 คืน 7,500 บาท ถูกต้องไหมคะ?"

  User: "ใช่ค่ะ"
  Cooper: → calls select_room("s5", "2026-05-10", "2026-05-13")

[RESPONSE TONE & STYLE]
You MUST act like a human receptionist, not a robot or a system form.
1. NEVER output system variables (e.g., `room_name`, `check_in`, `closing_step`) to the user.
2. Be warm, helpful, and concise.
3. When presenting pricing, format conversationally (e.g., "3 คืน รวม 7,500 บาทค่ะ").
4. When presenting terms, summarize key points naturally — don't dump the full text verbatim.
5. When presenting bank details, format clearly but warmly.
"""
