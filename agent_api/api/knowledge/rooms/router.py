from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db, require_auth
from api.knowledge.rooms.schemas import RoomCreate, RoomResponse, RoomUpdate
from api.knowledge.rooms.service import RoomManagementService
from db.models import Room as RoomModel

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    _: str = Depends(require_auth), db: AsyncSession = Depends(get_db)
) -> list[RoomModel]:
    return await RoomManagementService(db).list_rooms()


@router.get("/{id}", response_model=RoomResponse)
async def get_room(
    id: int, _: str = Depends(require_auth), db: AsyncSession = Depends(get_db)
) -> RoomModel:
    return await RoomManagementService(db).get_room(id)


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> RoomModel:
    return await RoomManagementService(db).create_room(data)


@router.patch("/{id}", response_model=RoomResponse)
async def update_room(
    id: int,
    data: RoomUpdate,
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> RoomModel:
    return await RoomManagementService(db).update_room(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    id: int, _: str = Depends(require_auth), db: AsyncSession = Depends(get_db)
) -> None:
    await RoomManagementService(db).delete_room(id)
