from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import Room as RoomModel, RoomPhoto
from api.rooms.repository import RoomRepository


class RoomService:
    """Async service that reads rooms data from Postgres."""

    async def get_all_rooms(self) -> list[RoomModel]:
        """Return all rooms from Postgres."""
        async with AsyncSessionLocal() as db:
            return await RoomRepository(db).get_all()

    async def get_room_by_name(self, room_name: str) -> RoomModel | None:
        """Look up a single room by its room_name (e.g. 'S1', 'V2')."""
        async with AsyncSessionLocal() as db:
            return await RoomRepository(db).get_by_name(room_name)

    async def get_valid_room_names(self) -> list[str]:
        """Return a list of all valid room names."""
        rooms = await self.get_all_rooms()
        return [r.room_name.lower() for r in rooms]

    async def does_room_exist(self, room_name: str) -> bool:
        """Check if a room name exists in the hotel."""
        return await self.get_room_by_name(room_name) is not None

    async def get_valid_rooms_list_str(self) -> str:
        """Get a comma-separated list of all valid rooms."""
        rooms = await self.get_all_rooms()
        return ", ".join(r.room_name.upper() for r in rooms)

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

    async def validate_room(self, room_name: str) -> str | None:
        """
        Returns an error message string if the room is invalid,
        or None if it is valid. This provides graceful tool errors.
        """
        if not await self.does_room_exist(room_name):
            valid = await self.get_valid_rooms_list_str()
            return f"Error: Room '{room_name}' does not exist. Please inform the user or choose from the valid rooms: {valid}"
        return None


room_service = RoomService()
