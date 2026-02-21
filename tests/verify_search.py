"""
Test script for search_rooms and run_search, using explicit search windows.

Usage:
    cd /Users/terwanchai/git/tatoh
    python tests/verify_search.py

Tests:
    1. search_rooms() directly — exact dates scenario
    2. search_rooms() directly — group usage
    3. run_search() via Criteria — normal flow
    4. run_search() via Criteria — exhausted (no rooms at all, forces expansion)
"""
import sys
import os
from dataclasses import asdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agent.room_evaluation.tools.search_rooms import search_rooms, RoomCard
from agent.room_evaluation.search import run_search, RunSearchResult
from agent.criteria_discovery.schema import Criteria


# ── Helpers ────────────────────────────────────────────────────────────────────

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_card(card: RoomCard, indent: str = "    "):
    print(f"{indent}Room:          {card.room_no} ({card.room_type})")
    print(f"{indent}Max guests:    {card.max_guests} | Requested: {card.requested_guests}")
    print(f"{indent}Extra bed req: {card.extra_bed_required}")
    if card.available_ranges:
        print(f"{indent}Avail ranges:  {card.available_ranges}")
        print(f"{indent}Nightly rates: {card.nightly_rates}")
    if card.pricing:
        print(f"{indent}Total price:   {card.pricing.total_price:,} THB")
        for item in card.pricing.breakdown:
            print(f"{indent}  {item.tier}: {item.nights} nights × {item.rate:,} = {item.subtotal:,}")
        if card.pricing.extra_bed:
            eb = card.pricing.extra_bed
            print(f"{indent}  Extra bed: {eb.nights} nights × {eb.rate} = {eb.subtotal:,}")
    print()

def print_search_result(rooms: list[RoomCard]):
    print(f"  ✓ Found ({len(rooms)} rooms):")
    if rooms:
        for card in rooms:
            print_card(card)
    else:
        print("    (none)\n")


# ── Test cases ─────────────────────────────────────────────────────────────────

def test_search_rooms_exact():
    """Scenario: couple, exact window — expect some results."""
    print_section("TEST 1 — search_rooms(): exact dates window, 2 guests")
    rooms = search_rooms(
        guests=2,
        search_start="2026-03-10",
        search_end="2026-03-12",
        duration_nights=2,
    )
    print_search_result(rooms)


def test_search_rooms_group():
    """Scenario: group of 6, looking at rooms — rooms that need extra beds will show extra_bed_req=True."""
    print_section("TEST 2 — search_rooms(): group of 6")
    rooms = search_rooms(
        guests=6,
        search_start="2026-03-10",
        search_end="2026-03-12",
        duration_nights=2,
    )
    print_search_result(rooms)
    # Rooms smaller than 6 should still appear (no guest-count filter drops them)
    small_rooms = [c for c in rooms if c.max_guests < 6]
    print(f"  Rooms smaller than 6 shown (multi-room use or extra bed): {len(small_rooms)}")


def test_run_search_normal():
    """Scenario: run_search() via Criteria — should use shift=0 if any results found."""
    print_section("TEST 3 — run_search(): exact mode via Criteria")
    criteria = Criteria(
        search_mode="exact",
        check_in_date="2026-03-15",
        check_out_date="2026-03-17",
        total_guests=2,
        duration_nights=2
    )
    criteria.auto_fill()
    print(f"  search_date_start: {criteria.search_date_start}")
    print(f"  search_date_end:   {criteria.search_date_end}")
    print(f"  criteria_id:       {criteria.get_criteria_id()}")
    result = run_search(criteria)
    assert isinstance(result, RunSearchResult)
    print(f"  Expanded days: {result.expanded_days}")
    print(f"  Exhausted:     {result.exhausted}")
    print_search_result(result.rooms)


def test_run_search_exhausted():
    """Scenario: dates far in the future where likely no PMS data — expect exhausted=True."""
    print_section("TEST 4 — run_search(): likely exhausted (far future dates)")
    criteria = Criteria(
        search_mode="exact",
        check_in_date="2030-01-01",
        check_out_date="2030-01-03",
        total_guests=2,
        duration_nights=2
    )
    criteria.auto_fill()
    result = run_search(criteria)
    print(f"  Expanded days: {result.expanded_days}")
    print(f"  Exhausted:     {result.exhausted}")
    print(f"  Found rooms:   {len(result.rooms)}")
    if result.exhausted:
        print("  ✓ Correctly reported exhausted — no rooms found within max expansion window")


def test_run_search_flexible():
    """Scenario: flexible mode — search_date_start/end used directly, unique criteria ID."""
    print_section("TEST 5 — run_search(): flexible mode")
    criteria = Criteria(
        search_mode="flexible",
        search_date_start="2026-03-01",
        search_date_end="2026-03-15",
        total_guests=2,
        duration_nights=3
    )
    criteria.auto_fill()
    print(f"  search_date_start: {criteria.search_date_start}")
    print(f"  search_date_end:   {criteria.search_date_end}")
    print(f"  criteria_id:       {criteria.get_criteria_id()}")
    result = run_search(criteria)
    print(f"  Expanded days: {result.expanded_days}")
    print(f"  Exhausted:     {result.exhausted}")
    print_search_result(result.rooms)

    # Verify different flexible searches produce different criteria IDs
    criteria2 = Criteria(
        search_mode="flexible",
        search_date_start="2026-04-01",
        search_date_end="2026-04-15",
        total_guests=2,
        duration_nights=3
    )
    criteria2.auto_fill()
    assert criteria.get_criteria_id() != criteria2.get_criteria_id(), \
        "Different flexible searches must produce different criteria IDs!"
    print(f"  ✓ criteria_id uniqueness verified: {criteria2.get_criteria_id()} != {criteria.get_criteria_id()}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        test_search_rooms_exact()
        test_search_rooms_group()
        test_run_search_normal()
        test_run_search_exhausted()
        test_run_search_flexible()
        print("\n" + "="*60)
        print("  All tests completed.")
        print("="*60)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] {e}")
        traceback.print_exc()
