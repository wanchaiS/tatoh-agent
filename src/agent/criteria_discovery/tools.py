from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from typing import Optional
import json

from agent.criteria_discovery.schema import Criteria


def _get_extraction_llm():
    """Lazy init to avoid import-time API key requirement."""
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return model.with_structured_output(Criteria)


def _build_extraction_prompt(current_criteria: Criteria, today: str) -> str:
    """Build the extraction prompt — same logic as the old node.py Stage 1."""
    return f"""
    You are a booking extraction assistant for Tatoh Resort.
    Current Date: {today}
    Current Parsed State: {json.dumps(current_criteria.model_dump(), indent=2)}

    ## SEARCH MODE REASONING:
    1. 'exact': User provides BOTH exact check-in and check-out dates, OR a fixed check-in with a duration.
       - Keywords/Patterns: "วันที่ 15-19", "เข้า 15 ออก 19", "จองวันที่", "ไปวันที่", "พักวันที่", "จอง... 1 คืน".
    2. 'flexible': User is not sure about exact dates or asks for availability in a broad period WITH a specific duration (or no specific dates at all).
       - Keywords/Patterns: "ช่วงวันที่... ถึง... 2 คืน", "ระหว่างวันที่... ว่างไหม", "เดือน...", "เดือนมีนาว่างไหม", "ช่วงเมษา".

    ## EXAMPLES:
    - User: "อยากจองพัก 2 คืน ช่วงวันที่ 10-15 พฤษภาค่ะ" (Duration provided within a window)
      Output: {{ "search_mode": "flexible", "search_date_start": "2026-05-10", "search_date_end": "2026-05-15", "duration_nights": 2 }}

    - User: "วันที่ 15-19 พฤษภาคะ" (Both check-in and check-out dates provided directly)
      Output: {{ "search_mode": "exact", "check_in_date": "2026-05-15", "check_out_date": "2026-05-19" }}

    - User: "ไปวันที่ 10 พฤษภา กลับวันที่ 12 ค่ะ"
      Output: {{ "search_mode": "exact", "check_in_date": "2026-05-10", "check_out_date": "2026-05-12" }}

    - User: "จองห้อง 26 กุมภา 1 คืนครับ 2 ท่าน"
      Output: {{ "search_mode": "exact", "check_in_date": "2026-02-26", "duration_nights": 1, "total_guests": 2 }}

    - User: "สอบถามราคาที่พัก ช่วงมีนาค่ะ ยังไม่แน่ใจวันค่ะ"
      Output: {{ "search_mode": "flexible", "search_date_start": "2026-03-01", "search_date_end": "2026-03-31" }}

    ## INSTRUCTIONS:
    1. Parse recent messages to extract criteria.
    2. Dates must be YYYY-MM-DD. Dates should not be in the past.
    3. If a month is mentioned without a year, and that month has already passed this year, assume the NEXT year.
       Example: If today is 2026-02-21 and user says "มกรา" → January 2027, not January 2026.
    4. If the user previously had a profile but their latest message strongly implies another mode, update the profile.
    5. Set 'is_year_ambiguous' to true ONLY if a specific past date is mentioned with a year that doesn't make sense.
    6. Set 'is_duration_confirmed' to true ONLY IF:
       - The user explicitly stated the number of nights (e.g. "2 คืน").
       - OR the user explicitly confirmed a check-out date you asked about.
       - If you just inferred the duration/check-out from ambiguous dates (like "15-19"), leave it false so Cooper can confirm it.
    """


def build_booking_tools(
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
    }

    # Keep last few messages for context (agent may strip context from query)
    recent_messages = messages[-6:] if len(messages) > 6 else messages

    @tool
    def extract_booking_criteria(query: str) -> str:
        """Extract booking information (dates, guests, rooms, duration) from
        the user's message. Call this when the user provides ANY booking-related
        information such as check-in/out dates, number of guests, preferred
        rooms, or duration of stay.

        Args:
            query: The user's message containing booking information.
        """
        prompt = _build_extraction_prompt(state["criteria"], today)
        criteria = _get_extraction_llm().invoke(
            [SystemMessage(content=prompt)] + recent_messages
        )

        if not criteria.search_mode:
            criteria.search_mode = "exact"

        criteria.auto_fill()
        state["criteria"] = criteria

        # Build response for the agent
        missing = criteria.get_missing_fields()
        errors = criteria.validate_data()
        is_year_ambiguous = criteria.is_year_ambiguous

        parts = []
        parts.append(f"Extracted: {json.dumps(criteria.model_dump(exclude_none=True), indent=2)}")

        if is_year_ambiguous:
            parts.append("Year is ambiguous — please ask the user to confirm the year.")
        if errors:
            parts.append(f"Validation errors: {errors}")
        if missing:
            parts.append(f"Still missing: {', '.join(missing)}")
        else:
            parts.append("All required criteria collected!")

        return "\n".join(parts)

    @tool
    def proceed_to_room_search() -> str:
        """Proceed to search for available rooms. Call this ONLY when all
        booking criteria have been collected AND confirmed with the user.
        Do NOT call if there are still missing fields."""

        criteria = state["criteria"]
        missing = criteria.get_missing_fields()
        errors = criteria.validate_data()
        is_year_ambiguous = criteria.is_year_ambiguous
        is_duration_confirmed = criteria.is_duration_confirmed

        if missing:
            return f"Cannot proceed — still missing: {', '.join(missing)}"
        if errors:
            return f"Cannot proceed — validation errors: {errors}"
        if is_year_ambiguous:
            return "Cannot proceed — year is ambiguous, please confirm with the user first."
        if not is_duration_confirmed:
            return "Cannot proceed — duration is not explicitly confirmed by the user. Please politely confirm how many nights they want to stay, or confirm their exact check-out date."

        state["transition_ready"] = True
        return "All criteria valid! Transitioning to room search."

    tools = [extract_booking_criteria, proceed_to_room_search]

    return (
        tools,
        lambda: state["transition_ready"],
        lambda: state["criteria"],
    )
