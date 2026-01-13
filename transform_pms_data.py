import json
from datetime import datetime, timedelta


def get_available_dates_by_room(json_file_path):
    """
    Transform PMS API response data into available dates by room.

    Args:
        json_file_path (str): Path to the PMS API response JSON file

    Returns:
        dict: Dictionary with date range and room availability
              Format: {
                  "from": "YYYY-MM-DD",
                  "to": "YYYY-MM-DD",
                  "rooms": {"roomNo": ["YYYY-MM-DD", ...]}
              }
    """
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    # Extract date range
    start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
    end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')

    # Generate all dates in range
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Build room ID to room number mapping
    room_id_to_number = {}
    for room in data['roomList']:
        room_id_to_number[room['id']] = room['roomNo']

    # Initialize result with all dates for each room
    result = {}
    for room_number in room_id_to_number.values():
        result[room_number] = set(all_dates)

    # Traverse reservationRoomList to collect reserved dates
    reservation_room_list = data.get('reservationRoomList', {})
    for room_type_id, rooms in reservation_room_list.items():
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
                            if reserved_date_str in result[room_number]:
                                result[room_number].discard(reserved_date_str)
                            current += timedelta(days=1)

    # Convert sets to sorted lists
    for room_number in result:
        result[room_number] = sorted(list(result[room_number]))

    # Format final output with date range
    return {
        "from": data['startDate'],
        "to": data['endDate'],
        "rooms": result
    }


if __name__ == '__main__':
    # Example usage
    result = get_available_dates_by_room('data/pms-api-response.json')

    # Print sample output
    print(f"Date range: {result['from']} to {result['to']}")
    print("\nAvailable dates by room:")
    for room_no, dates in sorted(result['rooms'].items()):
        print(f"\n{room_no}: {len(dates)} available dates")
        if dates:
            print(f"  First available: {dates[0]}")
            print(f"  Last available: {dates[-1]}")
            print(f"  Sample dates: {dates[:3]}")
