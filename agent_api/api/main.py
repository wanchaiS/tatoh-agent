import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


from core.config import STATIC_DIR
from agent.graph import graph
from agent.clients.pms_client import pms_client
from db.database import DATABASE_URL, engine
from api.auth.router import router as auth_router
from api.knowledge.rooms.router import router as rooms_router
from api.knowledge.rooms.photo_router import router as photo_router
from api.agent.runs import router as runs_router
from api.agent.threads import router as threads_router

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

@asynccontextmanager
async def lifespan(app: FastAPI):
    serde = JsonPlusSerializer(allowed_msgpack_modules=[('agent.graph', 'InternalRoom')])
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
async def ensure_guest_id(request: Request, call_next):
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


app.include_router(auth_router)
app.include_router(threads_router)
app.include_router(runs_router)
app.include_router(rooms_router)
app.include_router(photo_router)

# Mount static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
