import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AnyMessage
from pydantic import BaseModel

router = APIRouter()


class RunInput(BaseModel):
    input: dict | None = None
    stream_mode: list[str] | str = "values"
    assistant_id: str = "agent"


def _serialize(obj: object) -> object:
    """Make LangGraph output JSON-serializable."""
    if isinstance(obj, AnyMessage):
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


@router.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, body: RunInput, request: Request):
    """Stream a graph run, matching LangGraph Agent Server SSE format."""
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    run_id = str(uuid.uuid4())

    stream_modes = (
        body.stream_mode if isinstance(body.stream_mode, list) else [body.stream_mode]
    )

    async def event_generator():
        # First event is always metadata
        yield _sse_event("metadata", {"run_id": run_id})

        try:
            # When stream_mode is a list, astream yields (mode, data) tuples
            async for chunk in graph.astream(
                body.input,
                config,
                stream_mode=stream_modes,
            ):
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    mode, data = chunk
                else:
                    # Single stream mode — event type is the mode itself
                    mode = stream_modes[0]
                    data = chunk

                yield _sse_event(mode, data)
        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

        # Final event
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
