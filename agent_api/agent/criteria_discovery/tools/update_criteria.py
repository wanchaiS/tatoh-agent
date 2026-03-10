import json
from datetime import datetime
from typing import List, Optional

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.graph.ui import push_ui_message
from langgraph.types import Command

from agent.glossary import t

from agent.criteria_discovery.schema import Criteria, DateWindow

VAGUE_WINDOW_THRESHOLD_DAYS = 10
REQUIRED_FIELDS = ["date_windows", "duration_nights", "total_guests"]

from agent.services.room_service import room_service


def _parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _get_missing(candidate: Criteria) -> list[str]:
    missing = []
    if not candidate.date_windows:
        missing.append("date_windows")
    if not candidate.duration_nights:
        missing.append("duration_nights")
    if not candidate.total_guests:
        missing.append("total_guests")
    return missing


def _validate(
    windows: List[DateWindow],
    duration_nights: Optional[int],
    total_guests: Optional[int],
    requested_rooms: Optional[List[str]],
) -> list[str]:
    """
    Validate all incoming fields.
    Returns errors.
    - errors: hard failures — reject and don't persist.
    """
    errors = []

    # Guests
    if total_guests is not None and (total_guests < 1 or total_guests > 30):
        errors.append(
            f"Guest count ({total_guests}) should be at least 1 and likely less than 30."
        )

    # Duration
    if duration_nights is not None and duration_nights < 1:
        errors.append("duration_nights must be at least 1.")

    # Requested rooms
    if requested_rooms is not None:
        for room in requested_rooms:
            if not room_service.does_room_exist(room):
                errors.append(
                    f"Room {room} is not a valid room type. Valid room types are: {room_service.get_valid_rooms_list_str()}."
                )

    # Windows
    for i, w in enumerate(windows):
        label = f"Window {i + 1} ({w.start_date}–{w.end_date})"
        start_dt = _parse_date(w.start_date)
        end_dt = _parse_date(w.end_date)

        if not start_dt:
            errors.append(f"{label}: Invalid start_date format. Must be YYYY-MM-DD.")
            continue
        if not end_dt:
            errors.append(f"{label}: Invalid end_date format. Must be YYYY-MM-DD.")
            continue
        if end_dt <= start_dt:
            errors.append(f"{label}: end_date must be after start_date.")
            continue
        if start_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            errors.append(f"{label}: start_date is in the past.")
            continue

        window_days = (end_dt - start_dt).days

        if duration_nights is not None:
            if duration_nights > window_days:
                errors.append(
                    f"{label}: duration_nights ({duration_nights}) exceeds window span ({window_days} days). "
                    f"Ask user to confirm dates or duration."
                )

    return errors


@tool
def update_criteria(
    date_windows: Optional[List[dict]] = None,
    duration_nights: Optional[int] = None,
    total_guests: Optional[int] = None,
    requested_rooms: Optional[List[str]] = None,
    runtime: ToolRuntime = None,
) -> Command:
    """Update booking criteria with new values. Only pass the fields you want to change.

    Args:
        date_windows: List of date windows to check. Each item must have:
            - start_date (YYYY-MM-DD): start of the window
            - end_date (YYYY-MM-DD): end of the window
            All windows share the same duration_nights.
        duration_nights: Number of nights for the stay — applies to all windows.
        total_guests: Total number of guests including children.
        requested_rooms: List of room types requested by the user.
    """
    current: Criteria = runtime.state.get("criteria") or Criteria()
    parts = []

    # ── Parse incoming windows ────────────────────────────────────────
    incoming_windows: List[DateWindow] = []
    if date_windows:
        for raw in date_windows:
            try:
                incoming_windows.append(DateWindow(**raw))
            except Exception as e:
                return Command(
                    update={
                        "criteria_ready": False,  # failed validation should also reset validation result
                        "criteria_confirmed": False,
                        "messages": [
                            ToolMessage(
                                content=f"Error parsing window {raw}: {e}",
                                tool_call_id=runtime.tool_call_id,
                            )
                        ],
                    }
                )

    # ── Determine effective values for cross-validation ───────────────
    effective_duration = (
        duration_nights if duration_nights is not None else current.duration_nights
    )
    effective_guests = (
        total_guests if total_guests is not None else current.total_guests
    )
    effective_windows = incoming_windows if incoming_windows else current.date_windows
    effective_requested_rooms = (
        requested_rooms if requested_rooms is not None else current.requested_rooms
    )

    # ── Validate ──────────────────────────────────────────────────────
    errors = _validate(
        effective_windows,
        effective_duration,
        effective_guests,
        effective_requested_rooms,
    )

    if errors:
        parts.append("Rejected due to errors:")
        parts.extend(f"  Error: {e}" for e in errors)
        return Command(
            update={
                "criteria_ready": False,  # failed validation should also reset validation result
                "criteria_confirmed": False,
                "messages": [
                    ToolMessage(
                        content="\n".join(parts), tool_call_id=runtime.tool_call_id
                    )
                ],
            }
        )

    # ── Build and persist candidate ───────────────────────────────────
    updates = {}
    if incoming_windows:
        updates["date_windows"] = incoming_windows  # agent always passes the full list
    if duration_nights is not None:
        updates["duration_nights"] = duration_nights
    if total_guests is not None:
        updates["total_guests"] = total_guests
    if requested_rooms is not None:
        updates["requested_rooms"] = requested_rooms

    if not updates:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="No updates provided. Specify at least one field to update.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

    candidate = current.model_copy(update=updates)
    missing = _get_missing(candidate)

    parts.append(f"Updated: {json.dumps(updates, default=str)}")
    if missing:
        parts.append(f"Still missing: {', '.join(missing)}")
    else:
        parts.append(
            "All criteria ready. Present a natural, friendly summary of the booking criteria "
            "to the user and ask for their confirmation."
        )

    if not missing:
        lang = runtime.state.get("user_language", "th")
        push_ui_message(
            "suggested_answers",
            {
                "options": [
                    t("confirm_criteria", lang),
                    t("update_criteria", lang),
                ],
            },
        )

    # update criteria and set validation result
    return Command(
        update={
            "criteria": candidate,
            "criteria_ready": not bool(missing),
            "criteria_confirmed": False,
            "messages": [
                ToolMessage(content="\n".join(parts), tool_call_id=runtime.tool_call_id)
            ],
        }
    )
