from collections.abc import AsyncGenerator

from fastapi import Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph
