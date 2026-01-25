from datetime import datetime, timedelta
from typing import List

def format_date_ranges(combos: List[List[str]]) -> List[str]:
    """
    Converts a list of contiguous date sequences into a list of simplified date ranges.
    
    Args:
        combos: List of lists, where each inner list contains contiguous 'YYYY-MM-DD' strings.
        
    Returns:
        List of formatted strings: "YYYY-MM-DD to YYYY-MM-DD" or "YYYY-MM-DD"
    """
    if not combos:
        return []

    ranges = []
    for combo in combos:
        if not combo:
            continue
        if len(combo) == 1:
            ranges.append(combo[0])
        else:
            ranges.append(f"{combo[0]} to {combo[-1]}")

    return ranges
