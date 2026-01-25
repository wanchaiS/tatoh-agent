import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Ensuring src is in the path for imports
sys.path.append(os.path.abspath("src"))

from agent.tools.find_available_windows import find_available_windows

class TestDiscoveryLogic(unittest.TestCase):

    def setUp(self):
        self.base_room = {
            'room_type_name': 'Standard Room',
            'room_name': '101',
            'price_weekdays': 1000,
            'price_weekends': 1200,
            'price_weekends_holidays': 1200,
            'price_ny_songkran': 2000,
            'max_guests': 2,
            'image_token': '![room_picture:101]',
            'room_type_id': '1'
        }

    @patch('agent.tools.find_available_windows.get_room_availability')
    @patch('agent.tools.find_available_windows.read_spreadsheet_data')
    def test_find_windows_basic(self, mock_read, mock_get):
        mock_read.return_value = [self.base_room]
        # Available May 1, 2, 3, 4, 5. Wanted: 2 nights.
        mock_get.return_value = {
            'rooms': {
                '101': {'room_no': '101', 'dates': ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05']}
            }
        }
        
        # Searching May 1 to May 10 for 2 nights
        result = find_available_windows.func(
            search_start='2026-05-01', 
            search_end='2026-05-10', 
            duration=2, 
            guests=2
        )
        
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        room_data = result['results'][0]
        self.assertEqual(room_data['room_no'], '101')
        # Windows: May 1-5 allows stays starting on May 1, 2, 3, 4. (total 4 start dates)
        # format_date_ranges will group these.
        self.assertIn('available_windows', room_data)
        self.assertIn('2026-05-01 to 2026-05-04', room_data['available_windows'])

    @patch('agent.tools.find_available_windows.get_room_availability')
    @patch('agent.tools.find_available_windows.read_spreadsheet_data')
    def test_no_windows_found(self, mock_read, mock_get):
        mock_read.return_value = [self.base_room]
        # Only single days available, no 2 consecutive nights
        mock_get.return_value = {
            'rooms': {
                '101': {'room_no': '101', 'dates': ['2026-05-01', '2026-05-03', '2026-05-05']}
            }
        }
        
        result = find_available_windows.func(
            search_start='2026-05-01', 
            search_end='2026-05-10', 
            duration=2, 
            guests=2
        )
        self.assertIsNone(result['results'])

if __name__ == '__main__':
    unittest.main()
