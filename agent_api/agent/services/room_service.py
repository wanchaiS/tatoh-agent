import difflib

from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import Room, RoomPhoto
from api.rooms.repository import RoomRepository


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

    async def fuzzy_match_room_name(self, input_name: str) -> str | None:
        """Return the canonical room_name closest to input (case-insensitive, typo-tolerant), or None."""
        all_rooms = await self.get_all_rooms()
        lower_to_canonical = {r.room_name.lower(): r.room_name for r in all_rooms}
        normalized = input_name.strip().lower()
        matches = difflib.get_close_matches(normalized, lower_to_canonical.keys(), n=1, cutoff=0.6)
        return lower_to_canonical[matches[0]] if matches else None

    async def fuzzy_match_room_type(self, input_type: str) -> str | None:
        """Return the canonical room_type closest to input (case-insensitive, typo-tolerant), or None."""
        all_rooms = await self.get_all_rooms()
        lower_to_canonical = {r.room_type.lower(): r.room_type for r in all_rooms}
        normalized = input_type.strip().lower()
        matches = difflib.get_close_matches(normalized, lower_to_canonical.keys(), n=1, cutoff=0.6)
        return lower_to_canonical[matches[0]] if matches else None

    async def resolve_room_name(self, room_name: str) -> tuple[str | None, str | None]:
        """
        Resolve a (possibly misspelled/miscased) room name to its canonical form.
        Returns (canonical_name, None) on success, or (None, error_msg) on failure.
        Tries exact match first, then fuzzy match.
        """
        # Exact match (handles correct casing)
        room = await self.get_room_by_name(room_name)
        if room:
            return room.room_name, None
        # Fuzzy match (handles typos and wrong case)
        canonical = await self.fuzzy_match_room_name(room_name)
        if canonical:
            return canonical, None
        valid = await self.get_valid_rooms_list_str()
        return None, f"Room '{room_name}' not recognised. Valid rooms: {valid}"

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
        or None if it is valid.
        Deprecated: prefer resolve_room_name which also returns the canonical name.
        """
        _, error = await self.resolve_room_name(room_name)
        return error


room_service = RoomService()
