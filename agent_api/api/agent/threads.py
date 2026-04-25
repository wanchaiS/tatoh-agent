import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.agent.schemas import CreateThreadResponse, ThreadResponse, ThreadStateResponse
from api.dependencies import get_db, get_guest_id
from db.models import GuestThread

router = APIRouter(prefix="/api/threads")


@router.post("", response_model=CreateThreadResponse)
async def create_thread(
    guest_id: str = Depends(get_guest_id),
    db: AsyncSession = Depends(get_db),
) -> CreateThreadResponse:
    thread_id = str(uuid.uuid4())
    db.add(GuestThread(guest_id=guest_id, thread_id=thread_id))
    await db.commit()
    return CreateThreadResponse(thread_id=thread_id)


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    guest_id: str = Depends(get_guest_id),
    db: AsyncSession = Depends(get_db),
) -> list[ThreadResponse]:
    result = await db.execute(
        select(GuestThread)
        .where(GuestThread.guest_id == guest_id)
        .order_by(GuestThread.created_at.desc())
    )
    threads = result.scalars().all()
    return [
        ThreadResponse(
            thread_id=t.thread_id,
            title=t.title,
            created_at=t.created_at.isoformat(),
        )
        for t in threads
    ]


@router.get("/{thread_id}/state", response_model=ThreadStateResponse)
async def get_thread_state(
    thread_id: str, request: Request, _: str = Depends(get_guest_id)
) -> ThreadStateResponse:
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    return ThreadStateResponse(
        values=state.values,
        next=state.next,
        checkpoint=state.config.get("configurable", {}),
        created_at=state.created_at,
        parent_checkpoint=state.parent_config.get("configurable", {})
        if state.parent_config
        else None,
    )
