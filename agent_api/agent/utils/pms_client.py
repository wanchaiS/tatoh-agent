import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

import httpx
from dotenv import load_dotenv

from agent.utils.http_client import make_request

logger = logging.getLogger(__name__)


# ── Module State Type ─────────────────────────────────────────────────────────


class _PmsState(TypedDict):
    """Internal state for the PMS client module."""
    client: httpx.AsyncClient | None   # Lazily initialized HTTP client
    token: str | None                  # Current PMS access token
    token_expiry: float                # Unix timestamp when token expires
    lock: asyncio.Lock                 # Concurrency guard for token refresh
    base_url: str                      # PMS API base URL (no trailing slash)
    hotel_code: str | None             # Hotel identifier for PMS auth
    username: str | None               # PMS login username
    password: str | None               # PMS login password


# ── Raw PMS API Response Types ────────────────────────────────────────────────
# These mirror the JSON shape returned by GET /calendar/detail/{date}


class _PmsRawRoom(TypedDict):
    """A room entry from the PMS roomList array."""
    id: str            # PMS internal room ID
    roomNo: str        # Display room number (e.g. "S5", "V2")
    roomTypeId: str    # FK to room type


class _PmsRawRoomType(TypedDict):
    """A room type entry from the PMS roomTypeList array."""
    id: str     # PMS internal room type ID
    name: str   # Human-readable name (e.g. "Sea View Bungalow")


class _PmsRawReservation(TypedDict):
    """A single reservation entry from the PMS reservationRoomList."""
    checkIn: str    # Check-in date, YYYY-MM-DD
    checkOut: str   # Check-out date, YYYY-MM-DD


class _PmsRawResponse(TypedDict):
    """Raw JSON response from GET /calendar/detail/{date}."""
    startDate: str   # Window start, YYYY-MM-DD
    endDate: str     # Window end, YYYY-MM-DD
    roomList: list[_PmsRawRoom]
    roomTypeList: list[_PmsRawRoomType]
    # Nested: roomTypeId → roomId → dateKey → list of reservations
    reservationRoomList: dict[str, dict[str, dict[str, list[_PmsRawReservation]]]]
    version: NotRequired[str]


# ── Parsed Output Types (public) ─────────────────────────────────────────────


class PmsRoomAvailability(TypedDict):
    """A single room's availability data as parsed from the PMS response."""
    room_id: str          # PMS internal room ID
    room_no: str          # Room number, lowercased (e.g. "s5")
    room_type_id: str     # PMS internal room type ID
    room_type_name: str   # Human-readable room type (e.g. "Sea View Bungalow")
    dates: list[str]      # Available dates as sorted YYYY-MM-DD strings


class PmsAvailabilityWindow(TypedDict):
    """Parsed PMS availability for a 14-day window."""
    from_date: str                          # Window start, YYYY-MM-DD
    to_date: str                            # Window end, YYYY-MM-DD
    rooms: dict[str, PmsRoomAvailability]    # Keyed by lowercased room number
    version: str                            # PMS API version string


# ── Internal Parsing Type ─────────────────────────────────────────────────────


class _PmsRoomAvailabilityInternal(TypedDict):
    """Internal representation during parsing — dates as a set for O(1) discard."""
    room_id: str
    room_no: str
    room_type_id: str
    room_type_name: str
    dates: set[str]

# Find the project root (where .env should be)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_ROOT_DIR, ".env")

# Load environment variables
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    print(f"PMS Module: .env file not found at {_ENV_PATH}")

# --- Private Module State ---
_state: _PmsState = {
    "client": None,
    "token": os.getenv("PMS_ACCESS_TOKEN"),
    "token_expiry": 0,
    "lock": asyncio.Lock(),
    "base_url": os.getenv("PMS_BASE_URL", "").rstrip("/"),
    "hotel_code": os.getenv("PMS_HOTEL_CODE"),
    "username": os.getenv("PMS_USERNAME"),
    "password": os.getenv("PMS_PASSWORD"),
}


def _get_client() -> httpx.AsyncClient:
    """Get or create the async HTTP client."""
    if _state["client"] is None or _state["client"].is_closed:
        headers = {}
        if _state["token"]:
            headers = {
                "Authorization": f"Bearer {_state['token']}",
                "Access-Token": _state["token"],
            }
        _state["client"] = httpx.AsyncClient(headers=headers)
    return _state["client"]


if not _state["token"]:
    print("PMS Module: No token found in environment on startup.")

EXPECTED_PMS_VERSION = "1.62"


def _update_env_file(key: str, value: str) -> None:
    """Update the .env file with the given key-value pair."""
    if not os.path.exists(_ENV_PATH):
        print(f"PMS Module: Cannot update token, {_ENV_PATH} not found.")
        return

    with open(_ENV_PATH, "r") as f:
        lines = f.readlines()

    updated = False
    with open(_ENV_PATH, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            # Ensure there's a newline if we append
            if lines and not lines[-1].endswith("\n"):
                f.write("\n")
            f.write(f"{key}={value}\n")

    # Also update current environment
    os.environ[key] = value


async def login() -> None:
    """Authenticate with the PMS and update the module-level state."""
    async with _state["lock"]:
        # Double-check if another coroutine already updated the token
        if _state["token"] and time.time() < _state["token_expiry"] - 60:
            return

        print("PMS Module: Logging in to Hoteliers Guru to get new access token...")

        auth_data = {
            "hotelCode": _state["hotel_code"],
            "otp": "",
            "password": _state["password"],
            "userName": _state["username"],
        }

        # Call the login endpoint directly (don't use make_request to avoid recursion)
        client = _get_client()
        response = await client.post(
            f"{_state['base_url']}/auth", json=auth_data, timeout=15
        )
        response.raise_for_status()
        data = response.json()

        token = data.get("accessToken")
        _state["token"] = token

        # Default expiry to 1 hour if not specified
        expires_in = 3600
        _state["token_expiry"] = time.time() + expires_in

        # Update client headers for all future calls
        client.headers.update(
            {"Authorization": f"Bearer {token}", "Access-Token": token}
        )

        # Persist token to .env
        if token:
            _update_env_file("PMS_ACCESS_TOKEN", token)


async def fetch_room_availability_window(start_date: str) -> PmsAvailabilityWindow:
    """Fetch a single 14-day window of room availability from the PMS, starting from start_date."""
    try:
        url = f"{_state['base_url']}/calendar/detail/{start_date}"
        client = _get_client()
        api_response = await make_request(
            client=client, method="GET", url=url, login_cb=login
        )
        parsed_response = _parse_response(api_response)
        return parsed_response
    except Exception as e:
        logger.error(f"Unexpected error occured during room availability search: {e}")
        raise e


def _parse_response(response: _PmsRawResponse) -> PmsAvailabilityWindow:
    received_version = response.get("version", "1.0")
    try:
        # Extract date range
        start_dt = datetime.strptime(response["startDate"], "%Y-%m-%d")
        end_dt = datetime.strptime(response["endDate"], "%Y-%m-%d")

        # Generate all dates in range
        all_dates = []
        current_date = start_dt
        while current_date <= end_dt:
            all_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        # Build room ID to room number mapping
        room_id_to_number = {}
        for room in response.get("roomList", []):
            room_id_to_number[room["id"]] = room["roomNo"]

        # Initialize rooms availability
        rooms_availability: dict[str, _PmsRoomAvailabilityInternal] = {}
        room_list = response.get("roomList", [])
        for room_type in response.get("roomTypeList", []):
            rooms = [
                room for room in room_list if room["roomTypeId"] == room_type["id"]
            ]
            for room in rooms:
                room_no = room_id_to_number.get(room["id"]).lower()
                rooms_availability[room_no] = {
                    "room_id": room["id"],
                    "room_no": room_no,
                    "room_type_id": room["roomTypeId"],
                    "room_type_name": room_type["name"],
                    "dates": set(all_dates),
                }

        # Traverse reservationRoomList to collect reserved dates
        # Note: PMS returns [] (empty list) instead of {} when there are no reservations
        reservation_room_list = response.get("reservationRoomList", {})
        if not isinstance(reservation_room_list, dict):
            reservation_room_list = {}
        for room_type_id, rooms_dict in reservation_room_list.items():
            if not isinstance(rooms_dict, dict):
                continue
            for room_id, dates_dict in rooms_dict.items():
                room_number = room_id_to_number.get(room_id)
                if room_number:
                    room_number = room_number.lower()
                    for date_key, reservations in dates_dict.items():
                        for reservation in reservations:
                            check_in = datetime.strptime(
                                reservation["checkIn"], "%Y-%m-%d"
                            )
                            check_out = datetime.strptime(
                                reservation["checkOut"], "%Y-%m-%d"
                            )
                            current = check_in
                            while current < check_out:
                                reserved_date_str = current.strftime("%Y-%m-%d")
                                if (
                                    reserved_date_str
                                    in rooms_availability[room_number]["dates"]
                                ):
                                    rooms_availability[room_number]["dates"].discard(
                                        reserved_date_str
                                    )
                                current += timedelta(days=1)

        # Standardize output for single window
        for room_number in rooms_availability:
            rooms_availability[room_number]["dates"] = sorted(
                list(rooms_availability[room_number]["dates"])
            )

        # Build final output with list[str] dates
        final_rooms: dict[str, PmsRoomAvailability] = {
            room_no: {
                "room_id": info["room_id"],
                "room_no": info["room_no"],
                "room_type_id": info["room_type_id"],
                "room_type_name": info["room_type_name"],
                "dates": info["dates"],  # already sorted list[str] at this point
            }
            for room_no, info in rooms_availability.items()
        }

        return {
            "from_date": response.get("startDate", ""),
            "to_date": response.get("endDate", ""),
            "rooms": final_rooms,
            "version": received_version,
        }

    except Exception as e:
        if received_version != EXPECTED_PMS_VERSION:
            error_msg = f"Error parsing PMS response. [Expected: {EXPECTED_PMS_VERSION}, Received: {received_version}] Detail: {e}"
            raise Exception(error_msg)
        raise e
