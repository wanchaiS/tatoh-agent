import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Ensuring src is in the path for imports
sys.path.append(os.path.abspath("src"))

from agent.tools.check_room_availability import (
    _calculate_total_price, 
    check_room_availability,
    _is_perfect_room_size,
    _can_fit_but_extension_required
)

class TestRoomLogic(unittest.TestCase):

    def setUp(self):
        self.base_room = {
            'room_type_name': 'Standard Room',
            'room_name': '101',
            'room_no': '101',
            'price_weekdays': 1000,
            'price_weekends': 1200,
            'price_weekends_holidays': 1200,
            'price_ny_songkran': 2000,
            'max_guests': 2,
            'image_token': '![room_picture:101]',
            'room_type_id': '1'
        }

    # --- Unit Tests: Pricing Logic (Structured) ---

    def test_pricing_all_weekdays(self):
        start = datetime(2026, 10, 13)
        end = datetime(2026, 10, 15)
        pricing = _calculate_total_price(self.base_room, start, end, 2)
        self.assertEqual(pricing['total'], 2000)
        self.assertEqual(len(pricing['breakdown_items']), 1)
        self.assertEqual(pricing['breakdown_items'][0]['tier'], 'Weekday')
        self.assertEqual(pricing['breakdown_items'][0]['nights'], 2)

    def test_pricing_weekdays_and_weekend(self):
        start = datetime(2026, 10, 15)
        end = datetime(2026, 10, 19)
        pricing = _calculate_total_price(self.base_room, start, end, 2)
        self.assertEqual(pricing['total'], 4600)
        # Weekday: 1 (Thu), Weekend: 3 (Fri, Sat, Sun)
        tiers = {item['tier']: item for item in pricing['breakdown_items']}
        self.assertEqual(tiers['Weekday']['nights'], 1)
        self.assertEqual(tiers['Weekend']['nights'], 3)

    def test_pricing_extra_bed(self):
        start = datetime(2026, 10, 13)
        end = datetime(2026, 10, 16)
        pricing = _calculate_total_price(self.base_room, start, end, 3)
        # 3 nights @ 1000 + 3 nights extra bed @ 700 = 5100
        self.assertEqual(pricing['total'], 5100)
        self.assertIsNotNone(pricing['extra_bed'])
        self.assertEqual(pricing['extra_bed']['nights'], 3)
        self.assertEqual(pricing['extra_bed']['rate'], 700)

    # --- Integration Tests: Structured Results ---

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('agent.tools.check_room_availability.read_spreadsheet_data')
    def test_matching_perfect_structured(self, mock_read, mock_get):
        mock_read.return_value = [self.base_room]
        mock_get.return_value = {
            'rooms': {
                '101': {'room_no': '101', 'room_type_id': '1', 'room_type_name': 'Standard Room', 'dates': ['2026-10-14', '2026-10-15']}
            }
        }
        result = check_room_availability.func(guests=2, checkInDate='2026-10-14', checkOutDate='2026-10-16')
        self.assertEqual(result['match_type'], 'PerfectMatch')
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        room_data = result['results'][0]
        self.assertEqual(room_data['room_no'], '101')
        self.assertEqual(room_data['total_price'], 2000)

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('agent.tools.check_room_availability.read_spreadsheet_data')
    def test_matching_alternative_structured(self, mock_read, mock_get):
        mock_read.return_value = [self.base_room]
        mock_get.return_value = {
            'rooms': {
                '101': {'room_no': '101', 'room_type_id': '1', 'room_type_name': 'Standard Room', 'dates': ['2026-10-16', '2026-10-17']}
            }
        }
        result = check_room_availability.func(guests=2, checkInDate='2026-10-14', checkOutDate='2026-10-16')
        self.assertEqual(result['match_type'], 'DurationMatchAlternativeDates')
        room_data = result['results'][0]
        self.assertIn('available_ranges', room_data)
        self.assertIn('2026-10-16 to 2026-10-17', room_data['available_ranges'])

if __name__ == '__main__':
    unittest.main()
