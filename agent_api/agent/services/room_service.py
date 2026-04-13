from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Room, RoomPhoto
from db.repositories.room_repository import RoomRepository
from core.photo_helpers import build_photo_urls, EmbeddedPhoto
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

    async def get_all_photos_for_rooms(self, room_ids: list[int]) -> dict[int, list[EmbeddedPhoto]]:
        """Return all photos (url + thumbnails) per room, ordered by sort_order."""
        if not room_ids:
            return {}
        result = await self.db.execute(
            select(RoomPhoto)
            .where(RoomPhoto.room_id.in_(room_ids))
            .order_by(RoomPhoto.room_id, RoomPhoto.sort_order)
        )
        photos = result.scalars().all()
        out: dict[int, list[EmbeddedPhoto]] = {rid: [] for rid in room_ids}
        for p in photos:
            out[p.room_id].append(build_photo_urls(p.room_id, p.filename))
        return out