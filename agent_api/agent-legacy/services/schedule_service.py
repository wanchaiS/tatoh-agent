from db.database import AsyncSessionLocal
from db.models import BoatSchedule, BusSchedule
from db.repositories.schedule_repository import (
    BoatScheduleRepository,
    BusScheduleRepository,
)


def _boat_to_dict(s: BoatSchedule) -> dict:
    return {
        "origin": s.origin,
        "destination": s.destination,
        "departure": s.departure.strftime("%H:%M"),
        "arrival": s.arrival.strftime("%H:%M"),
        "type": s.type,
        "price": s.price,
        "infant_price": s.infant_price,
        "young_children_price": s.young_children_price,
        "is_vip": s.is_vip,
        "is_direct": s.is_direct,
    }


def _bus_to_dict(s: BusSchedule) -> dict:
    return {
        "origin": s.origin,
        "destination": s.destination,
        "departure": s.departure.strftime("%H:%M"),
        "arrival": s.arrival.strftime("%H:%M"),
        "price": s.price,
    }


class ScheduleService:
    """Async service for boat and bus schedule lookups from Postgres."""

    async def find_boat_schedules(self, origin: str, destination: str) -> list[dict]:
        async with AsyncSessionLocal() as db:
            schedules = await BoatScheduleRepository(db).search(origin, destination)
            return [_boat_to_dict(s) for s in schedules]

    async def find_bus_schedules(self, origin: str, destination: str) -> list[dict]:
        async with AsyncSessionLocal() as db:
            schedules = await BusScheduleRepository(db).search(origin, destination)
            return [_bus_to_dict(s) for s in schedules]

    async def get_supported_boat_locations(self) -> list[str]:
        async with AsyncSessionLocal() as db:
            return await BoatScheduleRepository(db).get_distinct_locations()

    async def get_supported_bus_locations(self) -> list[str]:
        async with AsyncSessionLocal() as db:
            return await BusScheduleRepository(db).get_distinct_locations()


schedule_service = ScheduleService()
