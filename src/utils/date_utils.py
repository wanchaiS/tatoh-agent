from datetime import datetime, timedelta
from typing import List

def format_date_ranges(date_list: List[str]) -> List[str]:
    """
    Converts a list of individual date strings into a list of simplified date ranges.
    
    Example: 
        ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-08'] 
        -> ['2026-11-02 to 2026-11-04', '2026-11-08']
        
    Args:
        date_list: List of strings in 'YYYY-MM-DD' format.
        
    Returns:
        List of formatted strings representing date ranges or single dates.
    """
    if not date_list:
        return []

    # Parse and sort dates
    try:
        dates = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in date_list])
    except ValueError as e:
        # In case of invalid date strings, we might want to return as is or handle it.
        # For now, let's assume valid dates or let the error bubble up if critical.
        raise ValueError(f"Invalid date format in list: {e}")

    ranges = []
    if not dates:
        return []

    start_date = dates[0]
    current_date = dates[0]

    for i in range(1, len(dates)):
        if dates[i] == current_date + timedelta(days=1):
            current_date = dates[i]
        else:
            # End current range
            if start_date == current_date:
                ranges.append(start_date.strftime('%Y-%m-%d'))
            else:
                ranges.append(f"{start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
            
            # Start new range
            start_date = dates[i]
            current_date = dates[i]

    # Add the last range
    if start_date == current_date:
        ranges.append(start_date.strftime('%Y-%m-%d'))
    else:
        ranges.append(f"{start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")

    return ranges
