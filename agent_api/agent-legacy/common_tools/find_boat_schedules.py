from typing import Dict, List, Literal

from agent.services.schedule_service import schedule_service
from langchain.tools import tool

Location = Literal[
    "bangkok",
    "chumphon",
    "hua hin",
    "koh phangan",
    "koh samui",
    "koh tao",
    "surat thani",
    "koh lanta",
    "koh phi phi",
    "krabi",
    "nakhon si thammarat",
    "phuket",
    "railay",
]


@tool
async def find_boat_schedules(req_origin: Location, req_destination: Location) -> List[Dict] | str:
    """
    Find boat schedules from origin to destination. Use for 'when' or route advice.
    The Location list is a guide — other Thai cities/islands may also be supported.

    RESPONSE GUIDANCE:
    Present results as a clear list. For each schedule, ALWAYS include:
    - Departure Time (from 'departure')
    - Origin and Destination
    - Price (from 'price')
    Example: "07:00 from Chumphon to Koh Tao - 750 THB"

    Note: young_children_price = 2-10y, infant_price = 0-1y
    """
    results = await schedule_service.find_boat_schedules(req_origin, req_destination)

    if not results:
        supported = await schedule_service.get_supported_boat_locations()
        return (
            f"No boat schedules found from '{req_origin}' to '{req_destination}'. "
            f"Supported locations: {', '.join(supported)}"
        )

    return results
