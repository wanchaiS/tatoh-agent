from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.root_graph import graph_builder
from server.config import DATABASE_URL
from server.routes.threads import router as threads_router
from server.routes.runs import router as runs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app.state.graph = graph_builder.compile(checkpointer=checkpointer)
        yield


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
