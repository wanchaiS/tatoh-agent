from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Room as RoomModel
from db.repositories.room_repository import RoomRepository
from api.knowledge.rooms.schemas import RoomCreate, RoomUpdate


class RoomManagementService:
    def __init__(self, db: AsyncSession):
        self.repo = RoomRepository(db)

    async def list_rooms(self) -> list[RoomModel]:
        return await self.repo.get_all()

    async def get_room(self, id: int) -> RoomModel:
        room = await self.repo.get_by_id(id)
        if room is None:
            raise HTTPException(status_code=404, detail=f"Room {id} not found")
        return room

    async def create_room(self, data: RoomCreate) -> RoomModel:
        if await self.repo.get_by_name(data.room_name) is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Room with name '{data.room_name}' already exists",
            )
        return await self.repo.create(data)

    async def update_room(self, id: int, data: RoomUpdate) -> RoomModel:
        room = await self.get_room(id)
        return await self.repo.update(room, data)

    async def delete_room(self, id: int) -> None:
        room = await self.get_room(id)
        await self.repo.delete(room)
