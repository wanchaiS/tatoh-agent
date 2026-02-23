from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
import json
from datetime import datetime

from agent.criteria_discovery.schema import Criteria
from agent.utils.tool_errors import handle_tool_error

def _get_extraction_llm():
    """Lazy init to avoid import-time API key requirement."""
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return model.with_structured_output(Criteria)

def _build_extraction_prompt(current_criteria: Criteria, today: str) -> str:
    """Build the extraction prompt"""

    return f"""
    You are a booking extraction assistant for Tatoh Resort.

    Your ONLY job is to extract explicit dates, numbers from the user's message. 
    DO NOT guess the user's intent, and DO NOT calculate missing fields (like duration) yourself. If a value is not explicitly stated, leave it null.
    
    Current Date: {today}
    Current Parsed State: {json.dumps(current_criteria.model_dump(), indent=2)}

    ## EXTRACTION RULES:
    1. **Date Formatting:** All dates must be YYYY-MM-DD. Ensure dates actually exist on the calendar (e.g., cap invalid dates to the last valid day of the month).
    2. **Day-Only Dates:** If the user only provides days (e.g., "วันที่ 25-28") and those days are ahead of the Current Date, assume the current month and current year.
    3. **Month-Only Dates:** If the user only provides a month (e.g., "เดือนมีนา"), set `search_date_start` to the 1st of that month and `search_date_end` to the last day of that month.
    4. **Missing Year (Future):** If a date or month is provided without a year, and that month is later in the current year, assume the current year.
    5. **Missing Year (Past):** If a date or month is provided without a year, and that month has ALREADY PASSED in the current year, assume the NEXT year AND set `is_year_ambiguous` to true.
    6. **Duration Constraint:** NEVER calculate `duration_nights` from the start and end dates. Only extract it if explicitly stated (e.g., "2 คืน", "คืนนึง"). Otherwise, leave it null.
    7. **Preferred Rooms:** If the user specifically asks for a room name or number (e.g., "ห้อง S8", "ห้อง V1"), extract it into `preferred_rooms`.
    8. **Guest Metadata:** If the user mentions details about the guests' ages, relationships, or needs (e.g., "ผู้สูงอายุ", "เด็กเล็ก", "wheelchair"), summarize this into the `guest_meta_data` string.

    ## EXAMPLES (Edge Cases):

    - User: "สวัสดีคะมีห้องว่างวันที่ 25-28มั้ยคะ" 
    Logic: Day-only. Ahead of current date (Feb 22). Assume current month. Do NOT calculate duration.
    Output: {{ "search_date_start": "2026-02-25", "search_date_end": "2026-02-28", "duration_nights": null, "preferred_rooms": null, "guest_meta_data": null, "is_year_ambiguous": false }}

    - User: "สอบถามช่วงมกราคมครับ" 
    Logic: Month-only. January has already passed this year (2026). Assume Jan 2027 and flag ambiguous.
    Output: {{ "search_date_start": "2027-01-01", "search_date_end": "2027-01-31", "duration_nights": null, "preferred_rooms": null, "guest_meta_data": null, "is_year_ambiguous": true }}

    - User: "อยากได้ห้อง S8 คืนนึงค่ะ พาแม่ที่อายุมากไปด้วย ผู้ใหญ่ 2" 
    Logic: Explicit room, explicit duration ("คืนนึง"), explicit metadata. No dates provided.
    Output: {{ "search_date_start": null, "search_date_end": null, "duration_nights": 1, "total_guests": 2, "preferred_rooms": ["S8"], "guest_meta_data": "Traveling with elderly mother", "is_year_ambiguous": false }}

    - User: "ไป 10-12 พฤษภาคม 4 คน มีเด็ก 2 ขวบ 1 คน" 
    Logic: Missing year, but May is in the future. Assume 2026. Summarize metadata.
    Output: {{ "search_date_start": "2026-05-10", "search_date_end": "2026-05-12", "duration_nights": null, "total_guests": 5, "preferred_rooms": null, "guest_meta_data": "Includes 1 toddler (2 years old)", "is_year_ambiguous": false }}

    - User: "มีห้อง V2 ว่างเดือนเมษาซัก 2 คืนไหมคะ"
    Logic: Month-only. Future month. Explicit duration and explicit room.
    Output: {{ "search_date_start": "2026-04-01", "search_date_end": "2026-04-30", "duration_nights": 2, "preferred_rooms": ["V2"], "guest_meta_data": null, "is_year_ambiguous": false }}
    """

def build_scoped_booking_tools(
    current_criteria: Criteria,
    messages: list,
    today: str,
):
    """
    Build procedural tools with closure over current criteria and recent messages.
    Returns (tools_list, is_transition_ready_fn, get_criteria_fn).
    """
    # Mutable container so tools can update criteria
    state = {
        "criteria": current_criteria,
        "transition_ready": False,
        "search_results": [],
        "expanded_days": 0,
    }

    # Keep last few messages for context (agent may strip context from query)
    recent_messages = messages[-6:] if len(messages) > 8 else messages

    @tool
    @handle_tool_error
    def extract_booking_criteria() -> str:
        """Extract booking information (dates, guests, rooms, duration) from
        the user's message. Call this when the user provides ANY booking-related
        information such as check-in/out dates, number of guests, preferred
        rooms, or duration of stay.
        """
        prompt = _build_extraction_prompt(state["criteria"], today)
        criteria = _get_extraction_llm().invoke(
            [SystemMessage(content=prompt)] + recent_messages
        )

        state["criteria"] = criteria

        # Build response for the agent
        missing = criteria.get_missing_fields()
        errors = criteria.validate_data()
        is_year_ambiguous = criteria.is_year_ambiguous

        parts = []
        parts.append(f"Extracted: {json.dumps(criteria.model_dump(exclude_none=True), indent=2)}")

        if is_year_ambiguous:
            parts.append("Year is ambiguous — please ask the user to confirm the year.")
        if not criteria.duration_nights and criteria.search_date_start and criteria.search_date_end:
            parts.append("Note: The duration of stay is not explicit. You MUST politely ask the user to confirm how many nights they want to stay.")
        if errors:
            parts.append(f"Validation errors: {errors}")
        if missing:
            parts.append(f"Still missing: {', '.join(missing)}")
        
        if not errors and not missing and not is_year_ambiguous:
            parts.append("All required criteria collected!")

        return "\n".join(parts)

    @tool
    @handle_tool_error
    async def proceed_to_room_search(config: RunnableConfig) -> str:
        """Proceed to search for available rooms. Call this ONLY when all
        booking criteria have been collected AND confirmed with the user.
        Do NOT call if there are still missing fields."""

        criteria = state["criteria"]
        missing = criteria.get_missing_fields()
        errors = criteria.validate_data()
        is_year_ambiguous = criteria.is_year_ambiguous

        if missing:
            return f"Cannot proceed — still missing: {', '.join(missing)}"
        if errors:
            return f"Cannot proceed — validation errors: {errors}"
        if is_year_ambiguous:
            return "Cannot proceed — year is ambiguous, please confirm with the user first."
        if not criteria.duration_nights:
            return "Cannot proceed — duration is missing. Please politely confirm how many nights they want to stay."

        state["transition_ready"] = True

        return (
            "All criteria validated! Tell the user politely that you have all the details "
            "and are now going to check the room availability for them. Do NOT tell them the results yet, "
            "just give a short, friendly confirmation that you're checking."
        )

    @tool
    @handle_tool_error
    def resolve_ambiguous_year(confirmed_year: int) -> str:
        """
        Call this tool ONLY when you have asked the user to confirm an ambiguous year (e.g., asking if they meant 2027) 
        and the user has confirmed or corrected it. Pass the final, correct 4-digit year (e.g., 2027 or 2026) 
        into this tool to update the system and remove the ambiguity.
        """
        criteria = state["criteria"]
        if not criteria.is_year_ambiguous:
            return "Error: The year is not currently flagged as ambiguous."

        # Reconstruct dates with the new year
        if criteria.search_date_start:
            old_start = datetime.strptime(criteria.search_date_start, "%Y-%m-%d")
            new_start = old_start.replace(year=confirmed_year)
            criteria.search_date_start = new_start.strftime("%Y-%m-%d")
            
        if criteria.search_date_end:
            old_end = datetime.strptime(criteria.search_date_end, "%Y-%m-%d")
            # Handle leap years if applicable
            try:
                new_end = old_end.replace(year=confirmed_year)
            except ValueError:
                # E.g. Feb 29 on a non-leap year
                from calendar import monthrange
                last_day = monthrange(confirmed_year, old_end.month)[1]
                new_end = old_end.replace(year=confirmed_year, day=last_day)
                
            criteria.search_date_end = new_end.strftime("%Y-%m-%d")

        criteria.is_year_ambiguous = False
        state["criteria"] = criteria

        return f"Successfully updated the year to {confirmed_year}. Updated Dates: {criteria.search_date_start} to {criteria.search_date_end}"

    tools = [extract_booking_criteria, proceed_to_room_search, resolve_ambiguous_year]

    return (
        tools,
        lambda: {
            "ready": state["transition_ready"],
        },
        lambda: state["criteria"],
    )