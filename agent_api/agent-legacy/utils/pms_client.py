import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, NotRequired

import httpx
from agent.utils.http_utils import make_request
from dotenv import load_dotenv
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


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


# Load environment variables
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_ROOT_DIR, ".env")

if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)
else:
    print(f"PMS Module: .env file not found at {_ENV_PATH}")

EXPECTED_PMS_VERSION = "1.62"


class PmsClient:
    """PMS API client. Singleton — holds auth token in memory, shares an httpx.AsyncClient."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client
        self.base_url: str = os.getenv("PMS_BASE_URL", "").rstrip("/")
        self.hotel_code: str | None = os.getenv("PMS_HOTEL_CODE")
        self.username: str | None = os.getenv("PMS_USERNAME")
        self.password: str | None = os.getenv("PMS_PASSWORD")
        self.token: str | None = None
        self.token_expiry: float = 0
        self._lock = asyncio.Lock()

    async def login(self) -> None:
        """Authenticate with the PMS and store the token in memory."""
        async with self._lock:
            # Double-check if another coroutine already refreshed the token
            if self.token and time.time() < self.token_expiry - 60:
                return

            logger.info("PMS: Logging in to get new access token...")

            auth_data = {
                "hotelCode": self.hotel_code,
                "otp": "",
                "password": self.password,
                "userName": self.username,
            }

            response = await self.http_client.post(
                f"{self.base_url}/auth", json=auth_data, timeout=15
            )
            response.raise_for_status()
            data = response.json()

            self.token = data.get("accessToken")
            self.token_expiry = time.time() + 3600

            # Update shared client headers for all future calls
            self.http_client.headers.update(
                {"Authorization": f"Bearer {self.token}", "Access-Token": self.token}
            )

    async def fetch_room_availability_window(self, start_date: str) -> Dict[str, Any]:
        """Fetch a single 14-day window of room availability from the PMS."""
        try:
            url = f"{self.base_url}/calendar/detail/{start_date}"
            api_response = await make_request(
                client=self.http_client, method="GET", url=url, login_cb=self.login
            )
            return self._parse_response(api_response)
        except Exception as e:
            logger.error(f"Unexpected error during room availability search: {e}")
            raise

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        received_version = response.get("version", "1.0")
        try:
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
                "from_date": response.get("startDate"),
                "to_date": response.get("endDate"),
                "rooms": rooms_availability,
                "version": received_version,
            }

        except Exception as e:
            if received_version != EXPECTED_PMS_VERSION:
                error_msg = f"Error parsing PMS response. [Expected: {EXPECTED_PMS_VERSION}, Received: {received_version}] Detail: {e}"
                raise Exception(error_msg)
            raise
