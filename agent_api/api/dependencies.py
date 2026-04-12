from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


def require_auth(request: Request) -> str:
    """FastAPI dependency — returns username from session cookie or raises 401."""
    from api.auth.service import decode_token  # avoid circular import at module load

    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Session expired")
    return username
