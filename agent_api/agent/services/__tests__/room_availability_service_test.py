from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from agent.services.room_availability_service import RoomAvailabilityService


def _make_pms_response(from_date: str, to_date: str, rooms: dict) -> dict:
    """Build a mock PMS response matching the structure from PmsClient._parse_response."""
    return {
        "from_date": from_date,
        "to_date": to_date,
        "rooms": rooms,
        "version": "1.62",
    }


def _make_room(
    room_id: str, room_no: str, room_type_id: str, room_type_name: str, dates: list[str]
) -> dict:
    """Build a single room entry in PMS response format."""
    return {
        "room_id": room_id,
        "room_no": room_no,
        "room_type_id": room_type_id,
        "room_type_name": room_type_name,
        "dates": dates,
    }


def _dates_range(start: str, days: int) -> list[str]:
    """Generate a list of consecutive date strings starting from `start`."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_pms_client():
    return AsyncMock()


@pytest.fixture
def service(mock_pms_client):
    svc = RoomAvailabilityService()
    svc.pms_client = mock_pms_client
    return svc


# ─── get_availability ────────────────────────────────────────────────────────
# This function is used by the search tool. It fetches room availability from PMS
# and caches results so repeated searches within the same turn don't hit PMS again.


class TestGetAvailability:
    # Scenario 1: Simple search that fits in one 14-day PMS window
    # Guest searches for 3 nights (Apr 10-13). PMS returns a 14-day window (Apr 9-22)
    # that fully covers the request. Should return both rooms with correct dates.
    @pytest.mark.asyncio
    async def test_simple_search_within_single_pms_window(
        self, service, mock_pms_client
    ):
        # Mock: PMS returns 2 rooms (S5 and V2), both fully available for 14 days
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-09", 14),
                    ),
                    "v2": _make_room(
                        "r2", "v2", "rt2", "Villa", _dates_range("2026-04-09", 14)
                    ),
                },
            )
        )

        result = await service.get_availability("2026-04-10", "2026-04-13")

        # Both rooms should be in the result
        assert "s5" in result
        assert "v2" in result
        # Dates should be clipped to only the 3 we asked for, not the full 14-day window
        assert result["s5"]["dates"] == {"2026-04-10", "2026-04-11", "2026-04-12"}
        assert result["v2"]["dates"] == {"2026-04-10", "2026-04-11", "2026-04-12"}
        # Should only call PMS once since the whole range fits in one window
        mock_pms_client.fetch_room_availability_window.assert_called_once()

    # Scenario 2: Result is clipped to only the dates we asked for
    # PMS always returns 14 days, but we only asked for 2 days (Apr 9-11).
    # Make sure we don't leak extra dates from the PMS window into the result.
    @pytest.mark.asyncio
    async def test_result_only_contains_requested_dates_not_full_window(
        self, service, mock_pms_client
    ):
        # Mock: PMS returns 14 days of availability for S5
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-09", 14),
                    )
                },
            )
        )

        result = await service.get_availability("2026-04-09", "2026-04-11")

        # Should only contain Apr 9 and Apr 10, even though PMS gave us 14 days
        assert result["s5"]["dates"] == {"2026-04-09", "2026-04-10"}

    # Scenario 3: Room has some nights booked — only free dates appear
    # Room S5 has reservations on Apr 10 and Apr 12 (PMS already excluded them).
    # We ask for Apr 9-13 — should only get back the dates that are actually free.
    @pytest.mark.asyncio
    async def test_partially_booked_room_returns_only_free_dates(
        self, service, mock_pms_client
    ):
        # Mock: PMS says S5 is only free on Apr 9 and Apr 11 (Apr 10 and 12 are booked)
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        ["2026-04-09", "2026-04-11"],
                    )
                },
            )
        )

        result = await service.get_availability("2026-04-09", "2026-04-13")

        # Only 2 of the 4 requested dates are free — the booked ones should not appear
        assert result["s5"]["dates"] == {"2026-04-09", "2026-04-11"}

    # Scenario 4: Long search that spans 2 PMS windows
    # Guest searches Apr 20-26, but one PMS window only covers 14 days (Apr 9-22).
    # Service needs to make a second PMS call to cover Apr 23-25.
    @pytest.mark.asyncio
    async def test_long_search_spanning_two_pms_windows(self, service, mock_pms_client):
        # Mock: first call covers Apr 9-22, second call covers Apr 23 - May 6
        mock_pms_client.fetch_room_availability_window.side_effect = [
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-09", 14),
                    )
                },
            ),
            _make_pms_response(
                "2026-04-23",
                "2026-05-06",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-23", 14),
                    )
                },
            ),
        ]

        result = await service.get_availability("2026-04-20", "2026-04-26")

        # Should have all 6 dates merged from both windows
        assert result["s5"]["dates"] == {
            "2026-04-20",
            "2026-04-21",
            "2026-04-22",
            "2026-04-23",
            "2026-04-24",
            "2026-04-25",
        }
        # Confirm it took 2 PMS calls to cover the full range
        assert mock_pms_client.fetch_room_availability_window.call_count == 2

    # Scenario 5: Second search overlaps first — should use cache, no extra API call
    # First search fetches Apr 9-22 from PMS. Second search asks for Apr 11-14
    # which is already covered by the cached window. PMS should not be called again.
    @pytest.mark.asyncio
    async def test_overlapping_search_reuses_cache(self, service, mock_pms_client):
        # Mock: PMS returns one 14-day window
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-09", 14),
                    )
                },
            )
        )

        # First call — fetches from PMS
        await service.get_availability("2026-04-10", "2026-04-13")
        # Second call — overlaps with first, should hit cache
        await service.get_availability("2026-04-11", "2026-04-14")

        # PMS should only be called once — the second call reused cached data
        mock_pms_client.fetch_room_availability_window.assert_called_once()

    # Scenario 6: PMS returns zero rooms
    # Maybe the hotel has no rooms configured, or something is wrong on PMS side.
    # Should return an empty dict without crashing.
    @pytest.mark.asyncio
    async def test_pms_returns_no_rooms(self, service, mock_pms_client):
        # Mock: PMS responds with a valid structure but no rooms at all
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-09",
                "2026-04-22",
                {},
            )
        )

        result = await service.get_availability("2026-04-10", "2026-04-13")

        # Should be empty, not None or an error
        assert result == {}


# ─── is_room_available ───────────────────────────────────────────────────────
# This function is used by the select tool. After the guest picks a room from
# search results, we call this to double-check with PMS that the room is still
# free RIGHT NOW. It always makes a fresh PMS call (no caching) because someone
# else could have booked the room between the search and the selection.


class TestIsRoomAvailable:
    # Scenario 1: Room is free for all requested nights
    # Guest picks room S5 for 3 nights (Apr 10-13). PMS confirms all 3 nights are free.
    @pytest.mark.asyncio
    async def test_room_free_for_all_nights(self, service, mock_pms_client):
        # Mock: PMS says S5 is fully available for the next 14 days
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-10", 14),
                    )
                },
            )
        )

        result = await service.is_room_available("s5", "2026-04-10", "2026-04-13")

        # All 3 nights are free — room is available
        assert result is True

    # Scenario 1b: Checkout date should NOT be counted as a required night
    # Guest checks in Apr 13, checks out Apr 15. They sleep in the room on Apr 13 and 14.
    # Apr 15 is checkout day — they leave that morning, so the room doesn't need to be free on the 15th.
    # Even though Apr 15 is booked by someone else, it should still return True.
    @pytest.mark.asyncio
    async def test_checkout_date_is_not_required(self, service, mock_pms_client):
        # Mock: PMS says S5 is free on Apr 13 and 14, but NOT on Apr 15 (booked by next guest)
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-13",
                "2026-04-26",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        ["2026-04-13", "2026-04-14"],
                    )
                },
            )
        )

        result = await service.is_room_available("s5", "2026-04-13", "2026-04-15")

        # Should be True — only Apr 13 and 14 are needed, Apr 15 is checkout (not a stay night)
        assert result is True

    # Scenario 2: One night got booked between search and selection
    # Guest picks room S5 for Apr 10-13, but Apr 11 got booked by someone else
    # in the time between searching and clicking "select".
    @pytest.mark.asyncio
    async def test_room_has_missing_night_in_range(self, service, mock_pms_client):
        # Mock: PMS says S5 is free on Apr 10 and Apr 12, but NOT Apr 11
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        ["2026-04-10", "2026-04-12"],
                    )
                },
            )
        )

        result = await service.is_room_available("s5", "2026-04-10", "2026-04-13")

        # Should be False — missing even 1 night means the room can't be booked
        assert result is False

    # Scenario 3: Room doesn't exist in PMS at all
    # Guest asks for room S5, but PMS only has room V2 in its response.
    # Could happen if the room was removed from PMS or there's a data mismatch.
    @pytest.mark.asyncio
    async def test_room_not_found_in_pms(self, service, mock_pms_client):
        # Mock: PMS only returns room V2, no S5
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {
                    "v2": _make_room(
                        "r2", "v2", "rt2", "Villa", _dates_range("2026-04-10", 14)
                    )
                },
            )
        )

        result = await service.is_room_available("s5", "2026-04-10", "2026-04-13")

        # Room S5 is not in the PMS response — can't book what doesn't exist
        assert result is False

    # Scenario 4: Guest types uppercase, PMS stores lowercase
    # Guest or frontend sends "S5" but PMS always returns "s5".
    # The lookup should be case-insensitive.
    @pytest.mark.asyncio
    async def test_room_name_case_mismatch(self, service, mock_pms_client):
        # Mock: PMS returns room as "s5" (lowercase)
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-10", 14),
                    )
                },
            )
        )

        # We pass "S5" (uppercase) — should still match
        result = await service.is_room_available("S5", "2026-04-10", "2026-04-13")

        # Should match despite case difference
        assert result is True

    # Scenario 5: Single night stay (edge case)
    # Guest only wants 1 night (check-in Apr 10, check-out Apr 11).
    # Only need Apr 10 to be free.
    @pytest.mark.asyncio
    async def test_single_night_stay(self, service, mock_pms_client):
        # Mock: PMS says S5 is free on Apr 10 only
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {
                    "s5": _make_room(
                        "r1", "s5", "rt1", "Sea View Bungalow", ["2026-04-10"]
                    )
                },
            )
        )

        result = await service.is_room_available("s5", "2026-04-10", "2026-04-11")

        # 1-night stay only needs 1 date — and it's free
        assert result is True

    # Scenario 6: Long stay spanning 2 PMS windows — all free
    # Guest wants Apr 30 - May 6 (6 nights). First PMS window covers up to May 3,
    # second window covers May 4 onwards. Both windows have the room free.
    @pytest.mark.asyncio
    async def test_long_stay_across_two_windows_all_free(
        self, service, mock_pms_client
    ):
        # Mock: two PMS windows, S5 is free in both
        mock_pms_client.fetch_room_availability_window.side_effect = [
            _make_pms_response(
                "2026-04-20",
                "2026-05-03",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-20", 14),
                    )
                },
            ),
            _make_pms_response(
                "2026-05-04",
                "2026-05-17",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-05-04", 14),
                    )
                },
            ),
        ]

        result = await service.is_room_available("s5", "2026-04-30", "2026-05-06")

        # Room is free across both windows — should be available
        assert result is True
        # Confirm it made 2 PMS calls (one per window)
        assert mock_pms_client.fetch_room_availability_window.call_count == 2

    # Scenario 7: Long stay spanning 2 PMS windows — second window is booked
    # Same long stay, but room S5 is fully booked in the second PMS window.
    @pytest.mark.asyncio
    async def test_long_stay_across_two_windows_second_booked(
        self, service, mock_pms_client
    ):
        # Mock: first window has S5 free, second window has S5 fully booked (empty dates)
        mock_pms_client.fetch_room_availability_window.side_effect = [
            _make_pms_response(
                "2026-04-20",
                "2026-05-03",
                {
                    "s5": _make_room(
                        "r1",
                        "s5",
                        "rt1",
                        "Sea View Bungalow",
                        _dates_range("2026-04-20", 14),
                    )
                },
            ),
            _make_pms_response(
                "2026-05-04",
                "2026-05-17",
                {"s5": _make_room("r1", "s5", "rt1", "Sea View Bungalow", [])},
            ),
        ]

        result = await service.is_room_available("s5", "2026-04-30", "2026-05-06")

        # First window is fine but second window has no dates — can't book the full stay
        assert result is False

    # Scenario 8: Room is completely booked (zero dates free)
    # Room S5 exists in PMS but every single night is reserved.
    @pytest.mark.asyncio
    async def test_room_fully_booked_zero_dates(self, service, mock_pms_client):
        # Mock: PMS returns S5 but with an empty dates list (all booked)
        mock_pms_client.fetch_room_availability_window.return_value = (
            _make_pms_response(
                "2026-04-10",
                "2026-04-23",
                {"s5": _make_room("r1", "s5", "rt1", "Sea View Bungalow", [])},
            )
        )

        result = await service.is_room_available("s5", "2026-04-10", "2026-04-13")

        # Room exists but has zero free dates — not available
        assert result is False

    # Scenario 9: Must not reuse cache from get_availability
    # get_availability already fetched and cached this date range, but is_room_available
    # must call PMS again to get real-time data. This is critical — a room could get
    # booked between the search and the selection.
    @pytest.mark.asyncio
    async def test_always_calls_pms_fresh_ignores_cache(self, service, mock_pms_client):
        # Mock: PMS returns the same response for both calls
        pms_response = _make_pms_response(
            "2026-04-10",
            "2026-04-23",
            {
                "s5": _make_room(
                    "r1",
                    "s5",
                    "rt1",
                    "Sea View Bungalow",
                    _dates_range("2026-04-10", 14),
                )
            },
        )
        mock_pms_client.fetch_room_availability_window.return_value = pms_response

        # First: get_availability caches this range (1 PMS call)
        await service.get_availability("2026-04-10", "2026-04-13")
        assert mock_pms_client.fetch_room_availability_window.call_count == 1

        # Second: is_room_available should call PMS again, NOT reuse cache
        await service.is_room_available("s5", "2026-04-10", "2026-04-13")
        # Total should be 2 — proving is_room_available made its own fresh call
        assert mock_pms_client.fetch_room_availability_window.call_count == 2
