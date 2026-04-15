from datetime import datetime

from agent.tools.exceptions import ToolValidationError
from agent.types import InternalRoom


def validate_dates(start_date: str, end_date: str):
    if start_date is None or end_date is None:
        raise ToolValidationError("start_date and end_date are required.")
    
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    if not start_dt:
        raise ToolValidationError("Invalid start_date format. Must be YYYY-MM-DD.")
    if not end_dt:
        raise ToolValidationError("Invalid end_date format. Must be YYYY-MM-DD.")
    if end_dt <= start_dt:
        raise ToolValidationError("end_date must be after start_date.")
    if start_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        raise ToolValidationError("start_date is in the past.")

def validate_room_names(internal_room_dict: dict[str, InternalRoom], room_names: list[str] | None = None):
    if not room_names:
        return None

    invalid_names = []
    
    for room in room_names:
        if room.lower() not in internal_room_dict:
            invalid_names.append(room)
    
    if invalid_names:
        valid = ", ".join(internal_room_dict.keys())
        raise ToolValidationError(f"Room(s) {', '.join(invalid_names)} not found. Available rooms: {valid}")
 

def parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None