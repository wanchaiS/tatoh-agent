import os
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, NotRequired
from utils.http_client import make_request

# --- Private Module State ---
# This dictionary is private to this module (prefixed with _)
_state = {
    "session": requests.Session(),
    "token": None,
    "token_expiry": 0,
    "lock": threading.Lock(),
    "base_url": os.getenv("PMS_BASE_URL", "https://pms-api.hoteliers.guru/api").rstrip("/"),
    "hotel_code": os.getenv("PMS_HOTEL_CODE"),
    "username": os.getenv("PMS_USERNAME"),
    "password": os.getenv("PMS_PASSWORD"),
}

EXPECTED_PMS_VERSION = "1.61"

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
            "userName": _state["username"]
        }
        
        # Call the login endpoint directly (don't use make_request to avoid recursion)
        response = _state["session"].post(
            f"{_state['base_url']}/auth",
            json=auth_data,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        _state["token"] = data.get("accessToken")
        
        # Default expiry to 1 hour if not specified (JWT 'exp' is available in token but we'll use a safe default)
        expires_in = 3600 
        _state["token_expiry"] = time.time() + expires_in
        
        # Update session headers for all future calls
        _state["session"].headers.update({
            "Authorization": f"Bearer {_state['token']}",
            "Access-Token": _state["token"]
        })

# --- Public API Functions ---

def get_room_availability(start_date: str) -> Dict[str, Any]:
    """
    Fetches room availability from the PMS starting from the given date.
    Returns availability for a 14-day window.
    """
    url = f"{_state['base_url']}/calendar/detail/{start_date}"
    
    data = make_request(
        session=_state["session"],
        method="GET",
        url=url,
        login_cb=login
    )

    received_version = data.get('version', '1.0') # Default to 1.0 if not present

    try:
        # Extract date range
        start_dt = datetime.strptime(data['startDate'], '%Y-%m-%d')
        end_dt = datetime.strptime(data['endDate'], '%Y-%m-%d')

        # Generate all dates in range
        all_dates = []
        current_date = start_dt
        while current_date <= end_dt:
            all_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        # Build room ID to room number mapping
        room_id_to_number = {}
        for room in data.get('roomList', []):
            room_id_to_number[room['id']] = room['roomNo']
        
        # Initialize rooms availability
        rooms_availability = {}
        room_list = data.get('roomList', [])
        for room_type in data.get('roomTypeList', []):
            rooms = [room for room in room_list if room['roomTypeId'] == room_type['id']]
            for room in rooms:  
                room_no = room_id_to_number.get(room['id'])
                rooms_availability[room_no] = {
                    "room_id": room['id'],
                    "room_no": room_no,
                    "room_type_id": room['roomTypeId'],
                    "room_type_name": room_type['name'],
                    "dates": set(all_dates)
                }

        # Traverse reservationRoomList to collect reserved dates
        reservation_room_list = data.get('reservationRoomList', {})
        for room_type_id, rooms in reservation_room_list.items():
            if not isinstance(rooms, dict):
                continue
            for room_id, dates_dict in rooms.items():
                # Get the room number for this room ID
                room_number = room_id_to_number.get(room_id)
                if room_number:
                    # For each date key, process all reservations
                    for date_key, reservations in dates_dict.items():
                        # Process each reservation in the array
                        for reservation in reservations:
                            check_in = datetime.strptime(reservation['checkIn'], '%Y-%m-%d')
                            check_out = datetime.strptime(reservation['checkOut'], '%Y-%m-%d')

                            # Reserve dates from checkIn to checkOut-1 (checkOut is available)
                            current = check_in
                            while current < check_out:
                                reserved_date_str = current.strftime('%Y-%m-%d')
                                if reserved_date_str in rooms_availability[room_number]['dates']:
                                    rooms_availability[room_number]['dates'].discard(reserved_date_str)
                                current += timedelta(days=1)

        # Convert sets to sorted lists
        for room_number in rooms_availability:
            rooms_availability[room_number]['dates'] = sorted(list(rooms_availability[room_number]['dates']))

        return {
            "from": data.get('startDate'),
            "to": data.get('endDate'),
            "rooms": rooms_availability,
            "version": received_version
        }

    except Exception as e:
        error_msg = f"Error parsing PMS response. [Expected Version: {EXPECTED_PMS_VERSION}, Received Version: {received_version}] Detail: {e}"
        if received_version != EXPECTED_PMS_VERSION:
            error_msg = f"PMS API Version Mismatch! The parser might be outdated. {error_msg}"
        print(error_msg)
        return {"from": start_date, "to": "", "rooms": {}, "error": error_msg, "version": received_version}
