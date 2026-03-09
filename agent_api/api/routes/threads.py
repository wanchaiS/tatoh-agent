import uuid

from fastapi import APIRouter, Request

router = APIRouter(prefix="/threads")


@router.post("")
async def create_thread():
    """Create a new thread. Returns a thread_id (UUID).

    No DB write needed — LangGraph creates the thread implicitly on first run.
    """
    return {"thread_id": str(uuid.uuid4())}


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str, request: Request):
    """Get the current state of a thread."""
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    return {
        "values": state.values,
        "next": state.next,
        "checkpoint": state.config.get("configurable", {}),
        "created_at": state.created_at,
        "parent_checkpoint": state.parent_config.get("configurable", {})
        if state.parent_config
        else None,
    }
