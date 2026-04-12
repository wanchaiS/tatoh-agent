from db.database import AsyncSessionLocal
from db.repositories.room_repository import RoomRepository


class RoomCache:
    """Minimal cache for room names and types, loaded once from DB."""

    def __init__(self) -> None:
        self._names: list[str] = []
        self._types: list[str] = []
        self._loaded: bool = False

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        async with AsyncSessionLocal() as db:
            rooms = await RoomRepository(db).get_all()
        self._names = [r.room_name for r in rooms]
        self._types = sorted({r.room_type for r in rooms})
        self._loaded = True

    async def get_room_names_str(self) -> str:
        await self._ensure_loaded()
        return ", ".join(self._names)

    async def get_room_types_str(self) -> str:
        await self._ensure_loaded()
        return ", ".join(self._types)

    async def is_valid_room_name(self, name: str) -> bool:
        await self._ensure_loaded()
        return name in self._names

    async def is_valid_room_type(self, room_type: str) -> bool:
        await self._ensure_loaded()
        return room_type in self._types


room_cache = RoomCache()
