from collections.abc import AsyncGenerator
from typing import Any, cast

from fastapi import HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        yield db


def get_graph(request: Request) -> CompiledStateGraph[Any, Any, Any, Any]:
    return cast(CompiledStateGraph[Any, Any, Any, Any], request.app.state.graph)


def get_guest_id(request: Request) -> str:
    guest_id = request.cookies.get("guest_id")
    if not guest_id:
        raise HTTPException(status_code=400, detail="Guest ID cookie missing")
    return guest_id


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
