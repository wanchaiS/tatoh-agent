from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BoatSchedule, BusSchedule


class BoatScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, origin: str, destination: str) -> list[BoatSchedule]:
        result = await self.db.execute(
            select(BoatSchedule).where(
                func.lower(BoatSchedule.origin) == origin.lower(),
                func.lower(BoatSchedule.destination) == destination.lower(),
            ).order_by(BoatSchedule.departure)
        )
        return result.scalars().all()

    async def get_distinct_locations(self) -> list[str]:
        origins = await self.db.execute(
            select(BoatSchedule.origin).distinct()
        )
        destinations = await self.db.execute(
            select(BoatSchedule.destination).distinct()
        )
        all_locs = set(origins.scalars().all()) | set(destinations.scalars().all())
        return sorted(all_locs)


class BusScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, origin: str, destination: str) -> list[BusSchedule]:
        result = await self.db.execute(
            select(BusSchedule).where(
                func.lower(BusSchedule.origin) == origin.lower(),
                func.lower(BusSchedule.destination) == destination.lower(),
            ).order_by(BusSchedule.departure)
        )
        return result.scalars().all()

    async def get_distinct_locations(self) -> list[str]:
        origins = await self.db.execute(
            select(BusSchedule.origin).distinct()
        )
        destinations = await self.db.execute(
            select(BusSchedule.destination).distinct()
        )
        all_locs = set(origins.scalars().all()) | set(destinations.scalars().all())
        return sorted(all_locs)
