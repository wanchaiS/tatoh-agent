from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Room, RoomPhoto
from db.repositories.room_repository import RoomRepository
from core.config import STATIC_URL_PREFIX
from sqlalchemy import func


class RoomService:
    """Async service that reads rooms data from Postgres using an injected session."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_rooms(self) -> list[Room]:
        """Return all rooms from Postgres."""
        return await RoomRepository(self.db).get_all()

    async def get_room_by_name(self, room_name: str) -> Room | None:
        """Look up a single room by its room_name (e.g. 'S1', 'V2')."""
        return await RoomRepository(self.db).get_by_name(room_name)

    async def get_first_photo_urls(self, room_ids: list[int]) -> dict[int, str | None]:
        """Return thumbnail URLs for multiple rooms in a single query."""
        if not room_ids:
            return {}
            
        # Subquery to get the min sort_order photo per room_id
        subq = (
            select(
                RoomPhoto.room_id,
                func.min(RoomPhoto.sort_order).label("min_order"),
            )
            .where(RoomPhoto.room_id.in_(room_ids))
            .group_by(RoomPhoto.room_id)
            .subquery()
        )
        result = await self.db.execute(
            select(RoomPhoto)
            .join(
                subq,
                (RoomPhoto.room_id == subq.c.room_id)
                & (RoomPhoto.sort_order == subq.c.min_order),
            )
        )
        photos = result.scalars().all()
        return {
            p.room_id: f"{STATIC_URL_PREFIX}/photos/rooms/{p.room_id}/thumbnails/{p.filename}"
            for p in photos
        }
