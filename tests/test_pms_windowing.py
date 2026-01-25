import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Ensuring src is in the path for imports
sys.path.append(os.path.abspath("src"))

from utils.pms_client import get_room_availability

class TestPMSWindowing(unittest.TestCase):

    @patch('utils.pms_client.make_request')
    def test_multi_window_merge(self, mock_make_request):
        # Setup mock responses for two 14-day windows
        # Window 1: 2026-05-01 to 2026-05-14
        # Window 2: 2026-05-15 to 2026-05-28
        
        def side_effect(session, method, url, login_cb, **kwargs):
            if "2026-05-01" in url: 
                return {
                    "startDate": "2026-05-01",
                    "endDate": "2026-05-14",
                    "version": "1.62",
                    "roomList": [{"id": "r1", "roomNo": "101", "roomTypeId": "t1"}],
                    "roomTypeList": [{"id": "t1", "name": "Standard"}],
                    "reservationRoomList": {} # All available
                }
            elif "2026-05-15" in url:
                return {
                    "startDate": "2026-05-15",
                    "endDate": "2026-05-28",
                    "version": "1.62",
                    "roomList": [{"id": "r1", "roomNo": "101", "roomTypeId": "t1"}],
                    "roomTypeList": [{"id": "t1", "name": "Standard"}],
                    "reservationRoomList": {
                        "t1": {
                            "r1": {
                                "2026-05-20": [{"checkIn": "2026-05-20", "checkOut": "2026-05-21"}]
                            }
                        }
                    }
                }
            return {}

        mock_make_request.side_effect = side_effect

        # Call the refactored function
        # search_start: 2026-05-01, search_end: 2026-05-25 (covers more than 14 days)
        result = get_room_availability("2026-05-01", "2026-05-25")

        # Verify results
        self.assertIn("rooms", result)
        self.assertIn("101", result["rooms"])
        
        dates = result["rooms"]["101"]["dates"]
        # Should contain dates from window 1 and window 2, EXCEPT 2026-05-20
        self.assertIn("2026-05-01", dates)
        self.assertIn("2026-05-15", dates)
        self.assertNotIn("2026-05-20", dates)
        self.assertIn("2026-05-21", dates)
        
        self.assertEqual(result["from"], "2026-05-01")
        self.assertEqual(result["to"], "2026-05-25")

    @patch('utils.pms_client.make_request')
    def test_31_day_restriction(self, mock_make_request):
        # search_start: 2026-05-01, search_end: 2026-06-10 (40 days)
        with self.assertRaises(ValueError) as cm:
            get_room_availability("2026-05-01", "2026-06-10")
        
        self.assertIn("Unexpected error occured", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
