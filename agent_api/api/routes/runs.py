import json
import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db, get_graph
from agent.context.agent_service_provider import AgentServiceProvider

logger = logging.getLogger(__name__)

router = APIRouter()

class RunInput(BaseModel):
    input: dict | None = None
    stream_mode: list[str] | str = ["values", "messages-tuple", "custom"]
    assistant_id: str = "agent"


def _serialize(obj: object) -> object:
    """Make LangGraph output JSON-serializable."""
    if isinstance(obj, BaseMessage):
        return obj.model_dump(mode="json")
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    return obj


def _sse_event(event: str, data: object) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(_serialize(data), default=str)}\n\n"


def _get_msg_type(msg) -> str:
    if isinstance(msg, BaseMessage):
        return msg.type
    if isinstance(msg, dict):
        return msg.get("type", "")
    return ""


def _has_tool_calls(msg) -> bool:
    if isinstance(msg, BaseMessage):
        return bool(getattr(msg, "tool_calls", None))
    if isinstance(msg, dict):
        return bool(msg.get("tool_calls"))
    return False

@router.post("/threads/{thread_id}/runs/stream")
async def stream_run(
    thread_id: str,
    body: RunInput,
    graph: CompiledStateGraph = Depends(get_graph),
    db: AsyncSession = Depends(get_db),
):
    """Stream a graph run, matching LangGraph Agent Server SSE format."""
    context = AgentServiceProvider(db_session=db)
    config = {"configurable": {"thread_id": thread_id}}
    run_id = str(uuid.uuid4())

    async def event_generator():
        yield _sse_event("metadata", {"run_id": run_id})

        try:
            async for chunk in graph.astream( # type: ignore[call-overload]
                body.input or {},
                config,
                stream_mode=["messages", "values", "custom"],
                version="v2",
                context=context,
            ):
                event_type = chunk["type"]
                data = chunk["data"]

                if event_type == "messages":
                    msg_chunk, metadata = data
                    # Only stream text content from the agent node
                    if not msg_chunk.content or metadata.get("langgraph_node") != "agent":
                        continue

                elif event_type == "values":
                    # Only send human + final ai messages (no tool-call ai) and ui
                    filtered_messages = [
                        m for m in data.get("messages", [])
                        if _get_msg_type(m) == "human"
                        or (_get_msg_type(m) == "ai" and not _has_tool_calls(m))
                    ]
                    data = {
                        "messages": filtered_messages,
                        "ui": data.get("ui", []),
                    }

                yield _sse_event(event_type, data)
        except Exception as e:
            logger.exception(f"Stream failed for thread {thread_id}")
            yield _sse_event("error", {"message": str(e)})

        yield _sse_event("end", None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
