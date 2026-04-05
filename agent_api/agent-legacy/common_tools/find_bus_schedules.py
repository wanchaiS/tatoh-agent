from typing import Dict, List, Literal

from langchain.tools import tool

from agent.services.schedule_service import schedule_service

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
async def find_bus_schedules(req_origin: Location, req_destination: Location) -> List[Dict] | str:
    """
    Find bus schedules from origin to destination.
    The Location list is a guide — other Thai cities may also be supported.

    RESPONSE GUIDANCE:
    Present results as a clear list. For each schedule, ALWAYS include:
    - Departure Time (from 'departure')
    - Origin and Destination
    - Price (from 'price')
    Example: "08:00 from Bangkok to Chumphon - 450 THB"
    """
    results = await schedule_service.find_bus_schedules(req_origin, req_destination)

    if not results:
        supported = await schedule_service.get_supported_bus_locations()
        return (
            f"No bus schedules found from '{req_origin}' to '{req_destination}'. "
            f"Supported locations: {', '.join(supported)}"
        )

    return results
