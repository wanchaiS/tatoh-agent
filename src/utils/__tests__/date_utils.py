import pytest
from utils.date_utils import format_date_ranges

def test_format_empty_list():
    assert format_date_ranges([]) == []

def test_format_single_date():
    assert format_date_ranges(['2026-11-02']) == ['2026-11-02']

def test_format_consecutive_dates():
    assert format_date_ranges(['2026-11-02', '2026-11-03', '2026-11-04']) == ['2026-11-02 to 2026-11-04']

def test_format_non_consecutive_dates():
    assert format_date_ranges(['2026-11-02', '2026-11-04', '2026-11-08']) == ['2026-11-02', '2026-11-04', '2026-11-08']

def test_format_mixed_dates():
    assert format_date_ranges(['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-08']) == ['2026-11-02 to 2026-11-04', '2026-11-08']

def test_format_unsorted_input():
    # Input is unsorted, but consecutive
    assert format_date_ranges(['2026-11-04', '2026-11-02', '2026-11-03']) == ['2026-11-02 to 2026-11-04']

def test_format_multiple_ranges():
    assert format_date_ranges([
        '2026-11-01', '2026-11-02', 
        '2026-11-05', 
        '2026-11-07', '2026-11-08', '2026-11-09'
    ]) == ['2026-11-01 to 2026-11-02', '2026-11-05', '2026-11-07 to 2026-11-09']

def test_invalid_date_format():
    with pytest.raises(ValueError, match="Invalid date format"):
        format_date_ranges(['invalid-date'])
