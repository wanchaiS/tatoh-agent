import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

import requests
from dotenv import load_dotenv

from agent.utils.http_client import make_request

logger = logging.getLogger(__name__)

# Find the project root (where .env should be)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_ROOT_DIR, ".env")

# Load environment variables
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    print(f"PMS Module: .env file not found at {_ENV_PATH}")

# --- Private Module State ---
# This dictionary is private to this module (prefixed with _)
_state = {
    "session": requests.Session(),
    "token": os.getenv("PMS_ACCESS_TOKEN"),
    "token_expiry": 0,
    "lock": threading.Lock(),
    "base_url": os.getenv("PMS_BASE_URL").rstrip("/"),
    "hotel_code": os.getenv("PMS_HOTEL_CODE"),
    "username": os.getenv("PMS_USERNAME"),
    "password": os.getenv("PMS_PASSWORD"),
}

# Initialize session headers if we already have a token
if _state["token"]:
    _state["session"].headers.update(
        {"Authorization": f"Bearer {_state['token']}", "Access-Token": _state["token"]}
    )
else:
    print("PMS Module: No token found in environment on startup.")

EXPECTED_PMS_VERSION = "1.62"


def _update_env_file(key: str, value: str):
    """
    Updates the .env file with the given key-value pair.
    """
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


def login():
    """
    Authenticates with the PMS and updates the module-level state.
    This is used as a callback by the http_client.
    """
    with _state["lock"]:
        # Double-check if another thread already updated the token
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
        response = _state["session"].post(
            f"{_state['base_url']}/auth", json=auth_data, timeout=15
        )
        response.raise_for_status()
        data = response.json()

        token = data.get("accessToken")
        _state["token"] = token

        # Default expiry to 1 hour if not specified (JWT 'exp' is available in token but we'll use a safe default)
        expires_in = 3600
        _state["token_expiry"] = time.time() + expires_in

        # Update session headers for all future calls
        _state["session"].headers.update(
            {"Authorization": f"Bearer {token}", "Access-Token": token}
        )

        # Persist token to .env
        if token:
            _update_env_file("PMS_ACCESS_TOKEN", token)


# TODO: Async Migration - Convert this function to `async def` and `await` the internal network calls.
def fetch_room_availability_window(start_date: str) -> Dict[str, Any]:
    """
    Fetches a single 14-day window of room availability from the PMS, starting from start_date.
    The response is not clipped, returning exactly what the PMS returns.
    """
    try:
        url = f"{_state['base_url']}/calendar/detail/{start_date}"
        api_response = make_request(
            session=_state["session"], method="GET", url=url, login_cb=login
        )
        parsed_response = _parse_response(api_response)
        return parsed_response
    except Exception as e:
        logger.error(f"Unexpected error occured during room availability search: {e}")
        raise e


def _parse_response(response: Dict[str, Any]) -> Dict[str, Any]:
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
        rooms_availability = {}
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

        return {
            "from": response.get("startDate"),
            "to": response.get("endDate"),
            "rooms": rooms_availability,
            "version": received_version,
        }

    except Exception as e:
        if received_version != EXPECTED_PMS_VERSION:
            error_msg = f"Error parsing PMS response. [Expected: {EXPECTED_PMS_VERSION}, Received: {received_version}] Detail: {e}"
            raise Exception(error_msg)
        raise e
