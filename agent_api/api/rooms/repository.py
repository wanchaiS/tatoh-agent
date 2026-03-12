from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Room as RoomModel
from api.rooms.schemas import RoomCreate, RoomUpdate


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[RoomModel]:
        result = await self.db.execute(select(RoomModel))
        return result.scalars().all()

    async def get_by_id(self, id: int) -> RoomModel | None:
        result = await self.db.execute(select(RoomModel).where(RoomModel.id == id))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> RoomModel | None:
        result = await self.db.execute(select(RoomModel).where(RoomModel.room_name == name))
        return result.scalars().first()

    async def create(self, data: RoomCreate) -> RoomModel:
        room = RoomModel(**data.model_dump())
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def update(self, room: RoomModel, data: RoomUpdate) -> RoomModel:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(room, key, value)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def delete(self, room: RoomModel) -> None:
        await self.db.delete(room)
        await self.db.commit()
