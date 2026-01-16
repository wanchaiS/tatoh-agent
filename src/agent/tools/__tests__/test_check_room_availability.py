import json
import unittest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Set a dummy key before importing anything that might initialize ChatOpenAI
os.environ["OPENAI_API_KEY"] = "dummy"

from agent.tools.check_room_availability import check_room_availability

class TestCheckRoomAvailability(unittest.TestCase):

    def setUp(self):
        # Mock room_list.json content
        self.mock_room_list = [
                {"room_id": "1", "room_type_id": "T1", "room_no": "S1", "room_type_name": "Type 1", "max_capacity": 2},
                {"room_id": "2", "room_type_id": "T1", "room_no": "S2", "room_type_name": "Type 1", "max_capacity": 2},
                {"room_id": "3", "room_type_id": "T2", "room_no": "F1", "room_type_name": "Type 2", "max_capacity": 4},
            ]

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_perfect_match_least_gap(self, mock_open, mock_get_availability):
        # Setup mock open for data/room_list.json
        mock_open.return_value.read.return_value = json.dumps(self.mock_room_list)
        
        # Scenario: 
        # S1 has a gap of 1 day before and 1 day after.
        # S2 has a gap of 0 days before and 0 days after.
        # Both are perfect matches for 2 guests on 2024-01-10 to 2024-01-12.
        
        availability_data = {
            "rooms": {
                "S1": {
                    "room_no": "S1",
                    "room_type_id": "T1",
                    "dates": ["2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12", "2024-01-13"]
                },
                "S2": {
                    "room_no": "S2",
                    "room_type_id": "T1",
                    "dates": ["2024-01-10", "2024-01-11"]
                }
            }
        }
        mock_get_availability.return_value = availability_data
        
        result = check_room_availability.invoke({"guests": 2, "checkInDate": "2024-01-10", "checkOutDate": "2024-01-12"})
        
        # Expectations based on CURRENT implementation:
        # S1 gap_before = 1 (2024-01-09), gap_after = 1 (2024-01-12 is available) -> Score = 2
        # S2 gap_before = 0, gap_after = 0 -> Score = 0
        # S2 should be the only perfect match chosen for Type T1.
        
        self.assertEqual(len(result['perfect_match']), 1)
        self.assertEqual(result['perfect_match'][0]['room_no'], "S2")

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_extension_required(self, mock_open, mock_get_availability):
        mock_open.return_value.read.return_value = json.dumps(self.mock_room_list)
        
        # Scenario: 3 guests for S1 (capacity 2). Should fit with extension bed (guests == max_capacity + 1)
        availability_data = {
            "rooms": {
                "S1": {
                    "room_no": "S1",
                    "room_type_id": "T1",
                    "dates": ["2024-01-10", "2024-01-11"]
                }
            }
        }
        mock_get_availability.return_value = availability_data
        
        result = check_room_availability.invoke({"guests": 3, "checkInDate": "2024-01-10", "checkOutDate": "2024-01-12"})
        
        # Currently the code returns 'date_matched_but_need_extension_bed'
        self.assertEqual(len(result['date_matched_but_need_extension_bed']), 1)
        self.assertEqual(result['date_matched_but_need_extension_bed'][0]['room_no'], "S1")

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_alternatives_short_circuit_mismatch(self, mock_open, mock_get_availability):
        mock_open.return_value.read.return_value = json.dumps(self.mock_room_list)
        
        # Scenario: S1 is available but too small (guests = 5, capacity = 2+1=3).
        # F1 is available but larger than required.
        
        availability_data = {
            "rooms": {
                "S1": {
                    "room_no": "S1",
                    "dates": ["2024-01-10", "2024-01-11"]
                },
                "F1": {
                    "room_no": "F1",
                    "room_type_id": "T2",
                    "dates": ["2024-01-10", "2024-01-11"]
                }
            }
        }
        mock_get_availability.return_value = availability_data
        
        result_1_guest = check_room_availability.invoke({"guests": 1, "checkInDate": "2024-01-10", "checkOutDate": "2024-01-12"})
        # S1, S2 should be perfect matches (True).
        # F1 has max_capacity 4. 4 - 1 = 3. 3 > 1. So it's NOT a perfect size.
        
        # Verify F1 is in alternatives
        alternative_rooms = [r.get('room_no') for r in result_1_guest['alternatives']]
        self.assertIn("F1", alternative_rooms)

    @patch('agent.tools.check_room_availability.get_room_availability')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_json_serializability(self, mock_open, mock_get_availability):
        mock_open.return_value.read.return_value = json.dumps(self.mock_room_list)
        availability_data = {
            "rooms": {
                "S1": {
                    "room_no": "S1",
                    "room_type_id": "T1",
                    "dates": ["2024-01-10"]
                }
            }
        }
        mock_get_availability.return_value = availability_data
        
        result = check_room_availability.invoke({"guests": 2, "checkInDate": "2024-01-10", "checkOutDate": "2024-01-11"})
        
        # This should NOT raise TypeError: Object of type set is not JSON serializable
        try:
            json_str = json.dumps(result)
            self.assertIsInstance(json_str, str)
            # Verify dates is a list
            parsed = json.loads(json_str)
            self.assertIsInstance(parsed['perfect_match'][0]['dates'], list)
        except TypeError as e:
            self.fail(f"Tool output is not JSON serializable: {e}")

if __name__ == '__main__':
    unittest.main()
