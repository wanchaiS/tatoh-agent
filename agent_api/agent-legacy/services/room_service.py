from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import Room, RoomPhoto
from db.repositories.room_repository import RoomRepository


class RoomService:
    """Async service that reads rooms data from Postgres."""

    async def get_all_rooms(self) -> list[Room]:
        """Return all rooms from Postgres."""
        async with AsyncSessionLocal() as db:
            return await RoomRepository(db).get_all()

    async def get_room_by_name(self, room_name: str) -> Room | None:
        """Look up a single room by its room_name (e.g. 'S1', 'V2')."""
        async with AsyncSessionLocal() as db:
            return await RoomRepository(db).get_by_name(room_name)

    async def get_first_photo_urls(self, room_ids: list[int]) -> dict[int, str | None]:
        """Return thumbnail URLs for multiple rooms in a single query."""
        if not room_ids:
            return {}
        async with AsyncSessionLocal() as db:
            from sqlalchemy import func
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
            result = await db.execute(
                select(RoomPhoto)
                .join(
                    subq,
                    (RoomPhoto.room_id == subq.c.room_id)
                    & (RoomPhoto.sort_order == subq.c.min_order),
                )
            )
            photos = result.scalars().all()
            return {
                p.room_id: f"/static/photos/rooms/{p.room_id}/thumbnails/{p.filename}"
                for p in photos
            }

    async def get_first_photo_url(self, room_id: int) -> str | None:
        """Return the thumbnail URL for the first photo of a room, or None."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RoomPhoto)
                .where(RoomPhoto.room_id == room_id)
                .order_by(RoomPhoto.sort_order)
                .limit(1)
            )
            photo = result.scalars().first()
            if photo:
                return f"/static/photos/rooms/{room_id}/thumbnails/{photo.filename}"
            return None


room_service = RoomService()
