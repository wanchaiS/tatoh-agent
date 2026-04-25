import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from agent.clients.pms_client import pms_client
from agent.graph import graph
from api.agent.runs import router as runs_router
from api.agent.threads import router as threads_router
from api.auth.router import router as auth_router
from api.knowledge.conversations.router import router as conversations_router
from api.knowledge.rooms.photo_router import router as photo_router
from api.knowledge.rooms.router import router as rooms_router
from core.config import STATIC_DIR
from db.database import DATABASE_URL, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[("agent.types", "InternalRoom")]
    )
    async with (
        AsyncPostgresSaver.from_conn_string(DATABASE_URL, serde=serde) as checkpointer,
        pms_client,
    ):
        await checkpointer.setup()
        app.state.graph = graph.compile(checkpointer=checkpointer)
        yield
    await engine.dispose()


app = FastAPI(title="Tatoh Agent Server", lifespan=lifespan)


@app.middleware("http")
async def ensure_guest_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response: Response = await call_next(request)
    if not request.cookies.get("guest_id"):
        response.set_cookie(
            "guest_id",
            str(uuid.uuid4()),
            httponly=True,
            samesite="lax",
            max_age=30 * 24 * 3600,
        )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(threads_router)
app.include_router(runs_router)
app.include_router(rooms_router)
app.include_router(photo_router)

# Mount static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
