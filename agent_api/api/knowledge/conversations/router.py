from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db, require_auth
from db.models import GuestThread

router = APIRouter(prefix="/api/conversations")

@router.get("")
async def list_all_conversations(
    page: int = 1,
    limit: int = 50,
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    total_result = await db.execute(select(func.count()).select_from(GuestThread))
    total = total_result.scalar_one()

    result = await db.execute(
        select(GuestThread).order_by(GuestThread.created_at.desc()).offset(offset).limit(limit)
    )
    threads = result.scalars().all()

    return {
        "threads": [
            {
                "thread_id": t.thread_id,
                "title": t.title,
                "created_at": t.created_at.isoformat(),
            }
            for t in threads
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
