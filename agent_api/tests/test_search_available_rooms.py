"""
Tests for search_available_rooms logic.

Mocks search_rooms_two to test pure decision logic without DB/PMS I/O.
Run: cd agent_api && .venv/bin/python -m pytest tests/test_search_available_rooms.py -v
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from agent.schemas import RoomCard
from agent.search_rooms import EXPANSION_STEPS
from agent.tools.discovery_criteria.update_criteria import (
    _can_accommodate,
    _validate_dates,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def make_room(name: str, max_guests: int, room_type: str = "Standard") -> RoomCard:
    return RoomCard(
        id=abs(hash(name)) % 10000,
        room_name=name,
        room_type=room_type,
        summary="test",
        bed_queen=1,
        bed_single=0,
        baths=1,
        size=30.0,
        price_weekdays=1000,
        price_weekends_holidays=1500,
        price_ny_songkran=2000,
        max_guests=max_guests,
        steps_to_beach=50,
        sea_view=3,
        privacy=3,
        steps_to_restaurant=30,
        room_design=3,
        room_newness=3,
    )


@dataclass
class FakeSearchResult:
    rooms: list
    expanded_days: int = 0
    exhausted: bool = False
    criteria_id: str = "test"


@dataclass
class FakeRuntime:
    tool_call_id: str = "test-call-id"
    state: dict = field(default_factory=dict)


EMPTY = FakeSearchResult(rooms=[])
FUTURE_START = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
FUTURE_END = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")


def _msg(result) -> str:
    msgs = result.update.get("messages", [])
    return msgs[0].content if msgs else ""


def _has_ui(result) -> bool:
    return "pending_ui" in result.update


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _call(mock_search, **kwargs):
    """Call the raw search_available_rooms coroutine, bypassing @tool wrapper."""
    from agent.tools.discovery_criteria.update_criteria import search_available_rooms

    defaults = dict(
        start_date=FUTURE_START,
        end_date=FUTURE_END,
        duration_nights=3,
        guest_no=None,
        requested_rooms=None,
        requested_room_types=None,
        runtime=FakeRuntime(),
    )
    defaults.update(kwargs)
    return await search_available_rooms.coroutine(**defaults)


# ── _validate_dates ──────────────────────────────────────────────────────────


class TestValidateDates:
    def test_valid_future_dates(self):
        assert _validate_dates(FUTURE_START, FUTURE_END) is None

    def test_none_start(self):
        assert _validate_dates(None, FUTURE_END) is not None

    def test_none_end(self):
        assert _validate_dates(FUTURE_START, None) is not None

    def test_bad_format_start(self):
        assert "format" in _validate_dates("bad", FUTURE_END).lower()

    def test_bad_format_end(self):
        assert "format" in _validate_dates(FUTURE_START, "bad").lower()

    def test_end_before_start(self):
        assert _validate_dates(FUTURE_END, FUTURE_START) is not None

    def test_same_dates(self):
        assert _validate_dates(FUTURE_START, FUTURE_START) is not None

    def test_past_start(self):
        past = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        assert "past" in _validate_dates(past, FUTURE_END).lower()


# ── _can_accommodate ─────────────────────────────────────────────────────────


class TestCanAccommodate:
    def test_single_room_enough(self):
        assert _can_accommodate([make_room("A", 4)], 5) is True  # 4+1=5

    def test_single_room_not_enough(self):
        assert _can_accommodate([make_room("A", 2)], 5) is False  # 2+1=3

    def test_multiple_rooms_enough(self):
        rooms = [make_room("A", 2), make_room("B", 2)]  # 3+3=6
        assert _can_accommodate(rooms, 5) is True

    def test_exact_match(self):
        rooms = [make_room("A", 2), make_room("B", 1)]  # 3+2=5
        assert _can_accommodate(rooms, 5) is True

    def test_not_enough_combined(self):
        rooms = [make_room("A", 1), make_room("B", 1)]  # 2+2=4
        assert _can_accommodate(rooms, 5) is False

    def test_empty_rooms(self):
        assert _can_accommodate([], 1) is False

    def test_zero_guests(self):
        assert _can_accommodate([], 0) is True

    def test_many_small_rooms(self):
        rooms = [make_room(f"R{i}", 1) for i in range(10)]  # 2*10=20
        assert _can_accommodate(rooms, 15) is True

    def test_many_small_rooms_not_enough(self):
        rooms = [make_room(f"R{i}", 1) for i in range(5)]  # 2*5=10
        assert _can_accommodate(rooms, 15) is False


# ── Validation branch ────────────────────────────────────────────────────────


class TestValidationBranch:
    @pytest.fixture(autouse=True)
    def _mock(self):
        with patch(
            "agent.tools.discovery_criteria.update_criteria.search_rooms_two",
            new_callable=AsyncMock,
        ) as m:
            self.mock = m
            yield

    def test_invalid_start_date(self):
        result = _run(_call(self.mock, start_date="bad"))
        assert "invalid" in _msg(result).lower() or "error" in _msg(result).lower()
        self.mock.assert_not_called()

    def test_end_before_start(self):
        result = _run(_call(self.mock, start_date=FUTURE_END, end_date=FUTURE_START))
        assert _msg(result)
        self.mock.assert_not_called()

    def test_missing_duration(self):
        result = _run(_call(self.mock, duration_nights=None))
        assert "duration" in _msg(result).lower()
        self.mock.assert_not_called()


# ── Approach 1: requested rooms/types (no expansion) ────────────────────────


class TestApproach1:
    @pytest.fixture(autouse=True)
    def _mock(self):
        with patch(
            "agent.tools.discovery_criteria.update_criteria.search_rooms_two",
            new_callable=AsyncMock,
        ) as m:
            self.mock = m
            yield

    def test_requested_room_found(self):
        self.mock.return_value = FakeSearchResult(rooms=[make_room("Room A", 2)])
        result = _run(_call(self.mock, requested_rooms=["Room A"]))
        assert "found" in _msg(result).lower()
        assert _has_ui(result)

    def test_requested_room_not_found(self):
        self.mock.return_value = FakeSearchResult(rooms=[make_room("Room B", 2)])
        result = _run(_call(self.mock, requested_rooms=["Room X"]))
        assert "no rooms" in _msg(result).lower()
        assert not _has_ui(result)

    def test_requested_room_type_found(self):
        self.mock.return_value = FakeSearchResult(rooms=[make_room("R1", 2, "Sea View")])
        result = _run(_call(self.mock, requested_room_types=["Sea View"]))
        assert "found" in _msg(result).lower()

    def test_requested_room_type_not_found(self):
        self.mock.return_value = FakeSearchResult(rooms=[make_room("R1", 2, "Garden")])
        result = _run(_call(self.mock, requested_room_types=["Sea View"]))
        assert "no rooms" in _msg(result).lower()

    def test_no_expansion_called(self):
        """Approach 1 calls search_rooms_two exactly once — no expansion."""
        self.mock.return_value = FakeSearchResult(rooms=[])
        _run(_call(self.mock, requested_rooms=["Room X"]))
        assert self.mock.call_count == 1


# ── Approach 2: no specific rooms, expansion loop ───────────────────────────


class TestApproach2:
    @pytest.fixture(autouse=True)
    def _mock(self):
        with patch(
            "agent.tools.discovery_criteria.update_criteria.search_rooms_two",
            new_callable=AsyncMock,
        ) as m:
            self.mock = m
            yield

    def test_rooms_found_no_expansion(self):
        """Rooms found at expansion=0 → return immediately."""
        rooms = [make_room("A", 2), make_room("B", 3)]
        self.mock.return_value = FakeSearchResult(rooms=rooms)

        result = _run(_call(self.mock, guest_no=4))
        msg = _msg(result)
        assert "found" in msg.lower()
        assert "expanded" not in msg.lower()
        assert _has_ui(result)
        # Only the initial shared call
        assert self.mock.call_count == 1

    def test_no_rooms_no_guest_asks_for_guest(self):
        """No rooms + guest_no=None → ask for guest_no."""
        self.mock.return_value = EMPTY
        result = _run(_call(self.mock, guest_no=None))
        assert "guest_no" in _msg(result).lower()
        # Only the initial shared call, no expansion attempted
        assert self.mock.call_count == 1

    def test_rooms_found_with_guest_no_returns_immediately(self):
        """Rooms found at expansion=0 with guest_no → returns rooms (Step 1)."""
        self.mock.return_value = FakeSearchResult(rooms=[make_room("A", 2)])
        result = _run(_call(self.mock, guest_no=2))
        assert "found" in _msg(result).lower()

    def test_combination_found_at_expansion_0(self):
        """No full-duration rooms, but 1-night search finds combinable rooms at expansion=0."""
        partial_rooms = [make_room("A", 2), make_room("B", 2)]  # capacity 3+3=6

        # Call sequence:
        # 1. initial search (duration=3) → empty (no full-duration rooms)
        # 2. Step 2 search (duration=1) at expansion=0 → partial_rooms
        self.mock.side_effect = [
            EMPTY,                                        # initial (duration=3)
            FakeSearchResult(rooms=partial_rooms),        # Step 2 (duration=1)
        ]

        result = _run(_call(self.mock, guest_no=5))
        msg = _msg(result)
        assert "can be combined" in msg.lower() or "combined" in msg.lower()
        assert _has_ui(result)
        # 2 calls: initial + Step 2 1-night search
        assert self.mock.call_count == 2

    def test_combination_not_enough_continues_to_expand(self):
        """1-night rooms at expansion=0 can't accommodate → expands to 3."""
        small_rooms = [make_room("A", 1)]  # capacity 2, need 5
        bigger_rooms = [make_room("A", 2), make_room("B", 2)]  # capacity 6

        self.mock.side_effect = [
            EMPTY,                                         # initial (duration=3)
            FakeSearchResult(rooms=small_rooms),           # Step 2 (duration=1) exp=0 — not enough
            EMPTY,                                         # expansion=3 (duration=3)
            FakeSearchResult(rooms=bigger_rooms),          # Step 2 (duration=1) exp=3 — enough
        ]

        result = _run(_call(self.mock, guest_no=5))
        msg = _msg(result)
        assert "combined" in msg.lower()
        assert "expanded" in msg.lower()
        assert self.mock.call_count == 4

    def test_rooms_found_after_first_expansion(self):
        """No rooms at expansion=0, full-duration rooms found at expansion=3."""
        rooms = [make_room("A", 2)]

        self.mock.side_effect = [
            EMPTY,                                    # initial (duration=3)
            EMPTY,                                    # Step 2 (duration=1) exp=0
            FakeSearchResult(rooms=rooms),            # expansion=3 (duration=3)
        ]

        result = _run(_call(self.mock, guest_no=2))
        msg = _msg(result)
        assert "found" in msg.lower()
        assert "expanded" in msg.lower()
        assert "±3" in msg

    def test_rooms_found_after_second_expansion(self):
        """No rooms at expansion=0,3 — found at expansion=5."""
        rooms = [make_room("A", 2)]

        self.mock.side_effect = [
            EMPTY,                                    # initial (duration=3)
            EMPTY,                                    # Step 2 (duration=1) exp=0
            EMPTY,                                    # expansion=3 (duration=3)
            EMPTY,                                    # Step 2 (duration=1) exp=3
            FakeSearchResult(rooms=rooms),            # expansion=5 (duration=3)
        ]

        result = _run(_call(self.mock, guest_no=2))
        msg = _msg(result)
        assert "±5" in msg

    def test_exhausted_all_expansions(self):
        """No rooms at any expansion → exhausted message."""
        # Each expansion step: 1 full-duration + 1 one-night = 2 calls per step
        # EXPANSION_STEPS = [0, 3, 5, 7] → initial + 7 more = 8 calls
        self.mock.return_value = EMPTY

        result = _run(_call(self.mock, guest_no=2))
        msg = _msg(result)
        assert "no rooms" in msg.lower() or "no combination" in msg.lower()
        assert str(EXPANSION_STEPS[-1]) in msg

    def test_expansion_dates_are_correct(self):
        """Verify expanded start/end dates are ±N days."""
        self.mock.return_value = EMPTY
        _run(_call(self.mock, guest_no=2))

        # Find the call for expansion=3 full-duration search (3rd call: after initial + Step2@exp0)
        calls = self.mock.call_args_list
        # expansion=3 full-duration call should have expanded dates
        expected_start = (datetime.strptime(FUTURE_START, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
        expected_end = (datetime.strptime(FUTURE_END, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")

        # Find a call matching the expanded dates
        found = any(
            c[0][0] == expected_start and c[0][1] == expected_end
            for c in calls if len(c[0]) >= 2
        )
        assert found, f"Expected call with dates ({expected_start}, {expected_end}) not found in {calls}"

    def test_rooms_found_no_guest_no_still_returns(self):
        """Rooms at expansion=0 with guest_no=None → Step 1 returns rooms."""
        self.mock.return_value = FakeSearchResult(rooms=[make_room("A", 2)])
        result = _run(_call(self.mock, guest_no=None))
        assert "found" in _msg(result).lower()
