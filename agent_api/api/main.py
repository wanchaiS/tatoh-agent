from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.graph import graph
from agent.clients.pms_client import pms_client
from db.database import DATABASE_URL, engine
from core.config import STATIC_DIR
from api.rooms.router import router as rooms_router
from api.rooms.photo_router import router as photo_router
from api.routes.runs import router as runs_router
from api.routes.threads import router as threads_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with (
        AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer,
        pms_client,
    ):
        await checkpointer.setup()
        app.state.graph = graph.compile(checkpointer=checkpointer)
        yield
    await engine.dispose()


app = FastAPI(title="Tatoh Agent Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threads_router)
app.include_router(runs_router)
app.include_router(rooms_router)
app.include_router(photo_router)

# Mount static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
